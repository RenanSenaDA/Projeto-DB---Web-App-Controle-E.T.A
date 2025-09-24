import os
import io
from datetime import datetime, timedelta, date

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from dotenv import load_dotenv

# === Carrega variáveis do .env automaticamente (funciona no VSCode/Windows) ===
load_dotenv()  # lê .env (se existir)

# ============================================================================ #
# Config / Constantes
# ============================================================================ #
st.set_page_config(page_title="ETA - Monitoramento", layout="wide")
st.title("🌊 ETA — Monitoramento e Qualidade da Água")

# Usa LOCAL_TZ; se não houver, tenta TZ; senão, Fortaleza como padrão
LOCAL_TZ = os.getenv("LOCAL_TZ", os.getenv("TZ", "America/Fortaleza"))
FEED_INTERVAL = int(os.getenv("FEED_INTERVAL", "5"))  # s

# BD (SQLAlchemy)
try:
    from sqlalchemy import create_engine, text
    HAVE_SQLA = True
except Exception:
    HAVE_SQLA = False

TAGS_PADRAO = [
    "qualidade/ph",
    "decantacao/turbidez",
    "bombeamento/vazao",
    "qualidade/cloro",
    "pressao/linha1",
    "nivel/reservatorio",
]
DEFAULT_UNITS = {
    "qualidade/ph": "pH",
    "decantacao/turbidez": "NTU",
    "bombeamento/vazao": "m³/h",
    "qualidade/cloro": "mg/L",
    "pressao/linha1": "bar",
    "nivel/reservatorio": "m",
}

# ============================================================================ #
# Conexão com o banco (Render/Neon via DATABASE_URL; fallback PG* em dev)
# ============================================================================ #
def get_db_url() -> str:
    """
    Prioriza DATABASE_URL (ex.: Render/Neon). Converte 'postgres://' e
    'postgresql://' para 'postgresql+psycopg2://' (SQLAlchemy).
    Fallback: PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE (dev/local).
    """
    url = os.getenv("DATABASE_URL")
    if url and url.strip():
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url

    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    user = os.getenv("PGUSER", "postgres")
    pwd  = os.getenv("PGPASSWORD", "postgres")
    db   = os.getenv("PGDATABASE", "eta")
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"

DB_URL = get_db_url()
USING_DATABASE_URL = bool(os.getenv("DATABASE_URL"))

# ============================================================================ #
# Infra BD
# ============================================================================ #
def ensure_db(db_url: str):
    if not HAVE_SQLA:
        raise RuntimeError("SQLAlchemy não está instalado.")
    engine = create_engine(db_url, pool_pre_ping=True)
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS eta;"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS eta.sensor(
              id   SERIAL PRIMARY KEY,
              tag  TEXT NOT NULL UNIQUE,
              unit TEXT,
              meta JSONB
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS eta.measurement(
              id        BIGSERIAL PRIMARY KEY,
              sensor_id INT NOT NULL REFERENCES eta.sensor(id) ON DELETE CASCADE,
              ts        TIMESTAMPTZ NOT NULL,
              value     DOUBLE PRECISION NOT NULL,
              quality   TEXT,
              meta      JSONB,
              CONSTRAINT uq_sensor_ts UNIQUE(sensor_id, ts)
            );
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_measurement_ts ON eta.measurement(ts);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_measurement_sensor_ts ON eta.measurement(sensor_id, ts DESC);"))
        for tag, unit in DEFAULT_UNITS.items():
            conn.execute(
                text("""
                  INSERT INTO eta.sensor(tag, unit)
                  VALUES (:tag, :unit)
                  ON CONFLICT(tag) DO NOTHING;
                """),
                {"tag": tag, "unit": unit},
            )

# ============================================================================ #
# Utils
# ============================================================================ #
def _sanitize(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df["ts"] = (
        pd.to_datetime(df["ts"], utc=True, errors="coerce")
          .dt.tz_convert(LOCAL_TZ)   # mostra no fuso local
          .dt.tz_localize(None)      # Plotly/Excel preferem naive
    )
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna(subset=["ts", "value"]).sort_values("ts")

@st.cache_data(ttl=5, show_spinner=False)
def load_from_db(db_url: str, start_dt: datetime) -> pd.DataFrame:
    if not HAVE_SQLA:
        raise RuntimeError("SQLAlchemy não está instalado.")
    engine = create_engine(db_url, pool_pre_ping=True)
    with engine.connect() as conn:
        q = text("""
            SELECT m.ts, s.tag, m.value, s.unit, m.quality, m.meta
            FROM eta.measurement m
            JOIN eta.sensor s ON s.id = m.sensor_id
            WHERE m.ts >= :start_dt
            ORDER BY m.ts ASC;
        """)
        res = conn.execute(q, {"start_dt": start_dt})
        df = pd.DataFrame(res.fetchall(), columns=["ts","tag","value","unit","quality","meta"])
    return _sanitize(df)

def fetch_period(db_url: str, start_utc: datetime, end_utc: datetime) -> pd.DataFrame:
    """Consulta bruta de um período fechado [start, end), já sanitizada."""
    engine = create_engine(db_url, pool_pre_ping=True)
    with engine.connect() as conn:
        q = text("""
            SELECT m.ts, s.tag, m.value, s.unit, m.quality, m.meta
            FROM eta.measurement m
            JOIN eta.sensor s ON s.id = m.sensor_id
            WHERE m.ts >= :start_dt AND m.ts < :end_dt
            ORDER BY m.ts ASC;
        """)
        res = conn.execute(q, {"start_dt": start_utc, "end_dt": end_utc})
        df = pd.DataFrame(res.fetchall(), columns=["ts","tag","value","unit","quality","meta"])
    return _sanitize(df)

def to_utc(ts_local: pd.Timestamp) -> datetime:
    return ts_local.tz_convert("UTC").to_pydatetime()

def compute_range(choice: str, custom_range: tuple[date, date] | None):
    """
    Constrói (start_utc, end_utc, label) a partir da escolha:
    - 'Últimos 30 dias' / '7 dias' / '1 dia'
    - 'Período específico' -> usa calendário (inicio, fim)
    """
    now_local = pd.Timestamp.now(tz=LOCAL_TZ)

    if choice == "Últimos 30 dias":
        start_local = now_local - pd.Timedelta(days=30)
        end_local = now_local
        label = "ultimos_30_dias"
    elif choice == "Últimos 7 dias":
        start_local = now_local - pd.Timedelta(days=7)
        end_local = now_local
        label = "ultimos_7_dias"
    elif choice == "Último 1 dia":
        start_local = now_local - pd.Timedelta(days=1)
        end_local = now_local
        label = "ultimo_1_dia"
    else:
        assert custom_range is not None and len(custom_range) == 2
        d_ini, d_fim = custom_range
        # [início 00:00, dia seguinte 00:00) no fuso local
        start_local = pd.Timestamp(d_ini, tz=LOCAL_TZ)
        end_local = pd.Timestamp(d_fim + timedelta(days=1), tz=LOCAL_TZ)
        label = f"{d_ini:%Y-%m-%d}_a_{d_fim:%Y-%m-%d}"

    return to_utc(start_local), to_utc(end_local), label

def build_excel_report(df: pd.DataFrame, label_periodo: str,
                       start_utc: datetime, end_utc: datetime) -> bytes:
    """Gera .xlsx com abas Resumo/Diario/Horario/Bruto."""
    def _autosize(ws, data: pd.DataFrame):
        for i, col in enumerate(data.columns):
            try:
                max_len = max(len(str(col)),
                              *(data[col].astype(str).map(len).tolist()))
            except Exception:
                max_len = 18
            ws.set_column(i, i, min(max_len + 2, 40))

    buf = io.BytesIO()

    with pd.ExcelWriter(buf, engine="xlsxwriter",
                        datetime_format="yyyy-mm-dd HH:MM:SS") as xw:
        if df.empty:
            vazio = pd.DataFrame({"aviso": [f"Sem dados para {label_periodo}."]})
            vazio.to_excel(xw, sheet_name="Resumo", index=False)
            _autosize(xw.sheets["Resumo"], vazio)
            return buf.getvalue()

        # colunas auxiliares (datas/horas locais)
        df["data"] = df["ts"].dt.date
        df["hora"] = df["ts"].dt.floor("h")

        # ----- Resumo -----
        last = df.sort_values("ts").groupby("tag", as_index=False).tail(1)
        resumo = (
            df.groupby("tag")
              .agg(**{
                  "Qtd de Leitura": ("value","count"),
                  "media": ("value","mean"),
                  "minimo": ("value","min"),
                  "maximo": ("value","max"),
              })
              .reset_index()
              .merge(
                  last[["tag","value","ts","unit"]],
                  on="tag", how="left"
              )
              .rename(columns={"value":"ultimo_valor",
                               "ts":"ultimo_ts",
                               "unit":"unidade"})
        )

        # ----- Diário -----
        diario = (
            df.groupby(["tag","data"], as_index=False)
              .agg(**{
                  "Qtd de Leitura": ("value","count"),
                  "media": ("value","mean"),
                  "minimo": ("value","min"),
                  "maximo": ("value","max"),
              })
              .sort_values(["tag","data"])
        )

        # ----- Horário -----
        horario = (
            df.groupby(["tag","hora"], as_index=False)
              .agg(**{
                  "Qtd de Leitura": ("value","count"),
                  "media": ("value","mean"),
                  "minimo": ("value","min"),
                  "maximo": ("value","max"),
              })
              .sort_values(["tag","hora"])
        )

        # ----- Bruto -----
        bruto = df[["ts","tag","unit","value","quality","meta"]].sort_values("ts")

        # Completude por tag = leituras observadas / leituras esperadas no intervalo
        seconds = max(0, int((end_utc - start_utc).total_seconds()))
        esperado = max(1, seconds // FEED_INTERVAL)
        resumo["completude_%"] = (
            resumo["Qtd de Leitura"] / esperado * 100
        ).clip(upper=100).round(1)

        # escreve e ajusta largura
        resumo.to_excel(xw, sheet_name="Resumo", index=False)
        diario.to_excel(xw, sheet_name="Diario", index=False)
        horario.to_excel(xw, sheet_name="Horario", index=False)
        bruto.to_excel(xw, sheet_name="Bruto", index=False)

        for name, data in [("Resumo", resumo), ("Diario", diario),
                           ("Horario", horario), ("Bruto", bruto)]:
            ws = xw.sheets[name]
            ws.freeze_panes(1, 1)
            _autosize(ws, data)

    return buf.getvalue()

# ============================================================================ #
# Visual
# ============================================================================ #
def make_kpi_cards(df: pd.DataFrame):
    latest = df.sort_values("ts").groupby("tag", as_index=False).tail(1)
    if latest.empty:
        st.info("Sem dados para o período selecionado.")
        return
    ncols = min(4, max(1, len(latest)))
    cols = st.columns(ncols)
    for i, row in enumerate(latest.itertuples(index=False)):
        with cols[i % ncols]:
            unit = getattr(row, "unit", None)
            label = f"{row.tag} ({unit})" if unit else f"{row.tag}"
            st.metric(label=label, value=f"{row.value:.3f}",
                      help=f"Última leitura em {row.ts:%d/%m %H:%M:%S}")

def _plotly_config():
    return {
        "displaylogo": False,
        "responsive": True,
        "modeBarButtonsToRemove": [
            "toggleSpikelines", "autoScale2d", "hoverCompareCartesian",
            "orbitRotation", "tableRotation", "lasso2d", "select2d"
        ],
    }

def charts_split(df: pd.DataFrame, tags: list[str]):
    import plotly.express as px
    if not tags:
        st.info("Selecione ao menos uma tag.")
        return
    ncols = 2 if len(tags) > 1 else 1
    cols = st.columns(ncols)
    for i, tag in enumerate(tags):
        dft = df[df["tag"] == tag].sort_values("ts")
        if dft.empty:
            continue
        unit = dft["unit"].dropna().iloc[0] if "unit" in dft and not dft["unit"].isna().all() else ""
        last = dft.iloc[-1]
        titulo_hora = f"{last['ts']:%d/%m %H:%M:%S}"
        title = f"{tag} ({unit}) • Último: {last['value']:.3f} às {titulo_hora}" if unit else \
                f"{tag} • Último: {last['value']:.3f} às {titulo_hora}"
        y_min, y_max = float(dft["value"].min()), float(dft["value"].max())
        pad = (y_max - y_min) * 0.08 if y_max > y_min else 1.0
        y_range = [y_min - pad, y_max + pad]
        fig = px.line(
            dft, x="ts", y="value",
            title=title,
            labels={"ts": "Tempo", "value": f"Valor ({unit})" if unit else "Valor"},
        )
        fig.update_traces(
            mode="lines+markers", marker=dict(size=4),
            hovertemplate="<b>%{y:.4f}</b><br>%{x}<extra></extra>",
            showlegend=False,
        )
        fig.update_layout(
            height=320, margin=dict(l=10, r=10, t=54, b=10),
            xaxis=dict(title=None, showgrid=True),
            yaxis=dict(range=y_range, showgrid=True, title=f"{unit}" if unit else "valor"),
        )
        with cols[i % ncols]:
            st.plotly_chart(fig, use_container_width=True, config=_plotly_config())

def layout(df: pd.DataFrame):
    st.subheader("KPIs (últimas leituras por tag)")
    make_kpi_cards(df)
    st.divider()
    st.subheader("Séries temporais")
    tags_sel = st.multiselect("Selecione as tags para plotar", TAGS_PADRAO, default=TAGS_PADRAO)
    charts_split(df, tags_sel)

# ============================================================================ #
# Sidebar / Run
# ============================================================================ #
st.sidebar.header("Banco de Dados")
if USING_DATABASE_URL:
    st.sidebar.success("Usando DATABASE_URL (Render/Produção)")
else:
    st.sidebar.warning("Usando variáveis PG* (Dev/Local)")

# período do viewer
date_range = st.sidebar.selectbox(
    "Período (viewer)",
    ["Últimos 15 min", "Últimas 2 h", "Últimas 24 h", "Últimos 7 dias"],
    index=2
)
if date_range.startswith("Últimos 15"):
    delta = timedelta(minutes=15)
elif date_range.startswith("Últimas 2"):
    delta = timedelta(hours=2)
elif date_range.startswith("Últimas 24"):
    delta = timedelta(hours=24)
else:
    delta = timedelta(days=7)
start = datetime.utcnow() - delta

# relatório Excel (períodos prontos / calendário)
st.sidebar.markdown("---")
st.sidebar.subheader("Relatório (Excel)")

rep_choice = st.sidebar.radio(
    "Período do relatório",
    ["Últimos 30 dias", "Últimos 7 dias", "Último 1 dia", "Período específico"],
    index=0
)
custom_range = None
if rep_choice == "Período específico":
    custom_range = st.sidebar.date_input(
        "Escolha o intervalo",
        value=(date.today() - timedelta(days=7), date.today()),
        format="DD/MM/YYYY"
    )
gen = st.sidebar.button("Gerar Excel")

# refresh configurável
refresh_s = st.sidebar.number_input("Atualização (s)", 1, 120, 5, 1)

st.caption(f"Fuso: {LOCAL_TZ}  •  Auto-refresh: {int(refresh_s)}s")
st_autorefresh(interval=int(refresh_s*1000), key="db_refresh")

try:
    ensure_db(DB_URL)
    # viewer
    df_view = load_from_db(DB_URL, start)
    if df_view.empty:
        st.warning("Sem dados no intervalo. Publique no MQTT/worker ou amplie o período.")
    else:
        layout(df_view)

    # relatório Excel
    if gen:
        start_utc, end_utc, label = compute_range(rep_choice, custom_range)
        df_period = fetch_period(DB_URL, start_utc, end_utc)
        xlsx_bytes = build_excel_report(df_period, label, start_utc, end_utc)
        fname = f"relatorio_ETA_{label}.xlsx"
        st.sidebar.success("Relatório pronto.")
        st.sidebar.download_button("Baixar Excel", data=xlsx_bytes, file_name=fname,
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

except Exception as e:
    st.error(f"Falha ao conectar/carregar: {e}")

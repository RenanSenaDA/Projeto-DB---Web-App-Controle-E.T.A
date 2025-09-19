# streamlit/streamlit_eta_app.py
import os
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# ------------------------------------------------------------
# Configuração da página (tem que ser o 1º comando do Streamlit)
# ------------------------------------------------------------
st.set_page_config(page_title="ETA - Monitoramento", layout="wide")
st.title("🌊 ETA — Monitoramento e Qualidade da Água")

# SQLAlchemy/psycopg2 (BD)
try:
    from sqlalchemy import create_engine, text
    HAVE_SQLA = True
except Exception:
    HAVE_SQLA = False

# Tags padrão exibidas no dashboard
TAGS_PADRAO = [
    "qualidade/ph",
    "decantacao/turbidez",
    "bombeamento/vazao",
    "qualidade/cloro",
    "pressao/linha1",
    "nivel/reservatorio",
]

# Unidades sugeridas para as tags padrão (ajuste se quiser)
DEFAULT_UNITS = {
    "qualidade/ph": "pH",
    "decantacao/turbidez": "NTU",
    "bombeamento/vazao": "m³/h",
    "qualidade/cloro": "mg/L",
    "pressao/linha1": "bar",
    "nivel/reservatorio": "m",
}

# ----------------- Bootstrap do BD -----------------
def ensure_db(db_url: str):
    """Garante schema/tabelas e cadastra sensores padrão."""
    if not HAVE_SQLA:
        raise RuntimeError("SQLAlchemy não está instalado.")
    engine = create_engine(db_url, pool_pre_ping=True)
    with engine.begin() as conn:
        # schema e tabelas
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS eta;"))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS eta.sensor (
                id   SERIAL PRIMARY KEY,
                tag  TEXT NOT NULL UNIQUE,
                unit TEXT,
                meta JSONB
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS eta.measurement (
                id         BIGSERIAL PRIMARY KEY,
                sensor_id  INTEGER NOT NULL REFERENCES eta.sensor(id) ON DELETE CASCADE,
                ts         TIMESTAMPTZ NOT NULL,
                value      DOUBLE PRECISION NOT NULL,
                quality    TEXT,
                meta       JSONB,
                CONSTRAINT uq_sensor_ts UNIQUE(sensor_id, ts)
            );
        """))

        # índices (se não existirem)
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_measurement_ts ON eta.measurement(ts);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_measurement_sensor_ts ON eta.measurement(sensor_id, ts DESC);
        """))

        # sensores padrão
        for tag, unit in DEFAULT_UNITS.items():
            conn.execute(
                text("""
                    INSERT INTO eta.sensor (tag, unit)
                    VALUES (:tag, :unit)
                    ON CONFLICT (tag) DO NOTHING;
                """),
                {"tag": tag, "unit": unit},
            )

# ----------------- Utils -----------------
def _sanitize(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza tipos e ordenação para evitar problemas nos gráficos."""
    if df.empty:
        return df
    ts = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    df["ts"] = ts.dt.tz_convert("UTC").dt.tz_localize(None)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["ts", "value"]).sort_values("ts")
    return df

@st.cache_data(ttl=5, show_spinner=False)
def load_from_db(db_url: str, start_dt: datetime) -> pd.DataFrame:
    """Busca leituras do período a partir do Postgres (cache expira em 5s)."""
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
        df = pd.DataFrame(
            res.fetchall(),
            columns=["ts", "tag", "value", "unit", "quality", "meta"],
        )
    return _sanitize(df)

def make_kpi_cards(df: pd.DataFrame):
    latest = df.sort_values("ts").groupby("tag", as_index=False).tail(1)
    if latest.empty:
        st.info("Sem dados para o período selecionado.")
        return
    ncols = max(1, min(4, len(latest)))
    cols = st.columns(ncols)
    for i, row in enumerate(latest.itertuples(index=False)):
        with cols[i % ncols]:
            unit = getattr(row, "unit", None)
            label = f"{row.tag} ({unit})" if unit else f"{row.tag}"
            st.metric(label=label, value=f"{row.value:.3f}", help=f"Última leitura em {row.ts}")

def make_charts(df: pd.DataFrame, tags_interesse: list[str]):
    import altair as alt  # import local para evitar erro se faltar pacote em outros scripts
    sub = df[df["tag"].isin(tags_interesse)].copy()
    if sub.empty:
        st.info("Sem dados para o período selecionado.")
        return

    sel = st.multiselect("Selecione as tags para plotar", tags_interesse, default=tags_interesse)

    for tag in sel:
        dft = sub[sub["tag"] == tag].copy().sort_values("ts")
        if dft.empty:
            continue
        has_unit = ("unit" in dft.columns) and (not dft["unit"].isna().all())
        title = f"{tag} ({dft['unit'].iloc[0]})" if has_unit else tag

        c = alt.Chart(dft).mark_line().encode(
            x=alt.X("ts:T", title="Tempo"),
            y=alt.Y("value:Q", title=title),
            tooltip=["ts:T", "value:Q", "unit:N"]
        ).properties(height=240)
        st.altair_chart(c, use_container_width=True)

def layout(df: pd.DataFrame):
    st.subheader("KPIs (últimas leituras por tag)")
    make_kpi_cards(df)
    st.divider()
    st.subheader("Séries temporais")
    make_charts(df, TAGS_PADRAO)

# ----------------- Sidebar / Config -----------------
st.sidebar.header("Banco de Dados (container)")
host = os.getenv("PGHOST", "localhost")
port = os.getenv("PGPORT", "5432")
user = os.getenv("PGUSER", "postgres")
pwd  = os.getenv("PGPASSWORD", "postgres")
db   = os.getenv("PGDATABASE", "eta")

date_range = st.sidebar.selectbox(
    "Período",
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
db_url = f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"

# Info + auto-refresh
st.caption(f"DB: {db}@{host}:{port}  •  Auto-refresh: 5s")
st_autorefresh(interval=5000, key="db_refresh")

# ----------------- Execução -----------------
try:
    ensure_db(db_url)  # garante schema/tabelas/sensores
    df = load_from_db(db_url, start)
    if df.empty:
        st.warning("Sem dados no intervalo. Publique no MQTT/worker ou amplie o período.")
    else:
        layout(df)
except Exception as e:
    st.error(f"Falha ao conectar/carregar: {e}")


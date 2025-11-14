import os
import io
from datetime import datetime, timedelta, date
from pathlib import Path

from alerts_email import enviar_alerta_para_destinatarios_padrao
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# tentamos importar o módulo de WhatsApp, mas não obrigamos
try:
    from alerts_whatsapp import enviar_alerta_whatsapp_para_destinatarios_padrao
    HAVE_WPP = True
except Exception:
    HAVE_WPP = False

# ------------------------- .env robusto -------------------------
from dotenv import load_dotenv, find_dotenv

# tenta achar um .env padrão acessível no PATH atual
load_dotenv(find_dotenv())
# tenta também caminhos relativos ao arquivo
_base_dir = Path(__file__).resolve().parent
for _extra in [_base_dir / ".env", _base_dir.parent / ".env", _base_dir.parent / "eta-stack" / ".env"]:
    if _extra.exists():
        load_dotenv(_extra, override=False)

# ------------------------- App base -------------------------
st.set_page_config(page_title="ETA - Monitoramento", layout="wide")
st.title("🌊 Plantsight — Monitoramento e Qualidade da Água")

LOCAL_TZ = os.getenv("LOCAL_TZ", os.getenv("TZ", "America/Fortaleza"))
FEED_INTERVAL = int(os.getenv("FEED_INTERVAL", "5"))

# SQLAlchemy
try:
    from sqlalchemy import create_engine, text
    HAVE_SQLA = True
except Exception:
    HAVE_SQLA = False

# Auth (passlib)
try:
    from passlib.hash import pbkdf2_sha256, bcrypt
    HAVE_PASSLIB = True
except Exception:
    HAVE_PASSLIB = False

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
ALERT_DEFAULTS = {
    "qualidade/ph": 7.00,
    "decantacao/turbidez": 5.00,
    "bombeamento/vazao": 500.00,
    "qualidade/cloro": 2.00,
    "pressao/linha1": 6.00,
    "nivel/reservatorio": 10.00,
}

# ------------------------- Helpers DB -------------------------
def to_sqlalchemy_url(url: str) -> str:
    if not url:
        return url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://") and "postgresql+psycopg://" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def get_db_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return to_sqlalchemy_url(url)
    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    user = os.getenv("PGUSER", "postgres")
    pwd = os.getenv("PGPASSWORD", "postgres")
    db = os.getenv("PGDATABASE", "eta")
    return f"postgresql+psycopg://{user}:{pwd}@{host}:{port}/{db}"


DB_URL = get_db_url()
USING_DATABASE_URL = bool(os.getenv("DATABASE_URL", "").strip())


# ------------------------- Password helpers -------------------------
def hash_password(plain: str) -> str:
    # novo padrão: pbkdf2_sha256 (sem limite prático)
    return pbkdf2_sha256.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        if hashed.startswith("$pbkdf2-sha256$"):
            return pbkdf2_sha256.verify(plain, hashed)
        else:
            # assume bcrypt para qualquer outro prefixo ($2b$, $2a$...)
            return bcrypt.verify(plain, hashed)
    except Exception:
        return False


# ------------------------- Infra BD (+ seed) -------------------------
def ensure_db(db_url: str):
    if not HAVE_SQLA:
        raise RuntimeError("SQLAlchemy não está instalado.")
    engine = create_engine(db_url, pool_pre_ping=True)
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS eta;"))
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS eta.sensor(
              id   SERIAL PRIMARY KEY,
              tag  TEXT NOT NULL UNIQUE,
              unit TEXT,
              meta JSONB
            );
        """
            )
        )
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS eta.measurement(
              id        BIGSERIAL PRIMARY KEY,
              sensor_id INT NOT NULL REFERENCES eta.sensor(id) ON DELETE CASCADE,
              ts        TIMESTAMPTZ NOT NULL,
              value     DOUBLE PRECISION NOT NULL,
              quality   TEXT,
              meta      JSONB,
              CONSTRAINT uq_sensor_ts UNIQUE(sensor_id, ts)
            );
        """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_measurement_ts ON eta.measurement(ts);"))
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_measurement_sensor_ts ON eta.measurement(sensor_id, ts DESC);")
        )
        for tag, unit in DEFAULT_UNITS.items():
            conn.execute(
                text(
                    """INSERT INTO eta.sensor(tag, unit)
                        VALUES (:tag, :unit) ON CONFLICT(tag) DO NOTHING;"""
                ),
                {"tag": tag, "unit": unit},
            )

        # Tabela de usuários
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS eta.app_user(
              id            SERIAL PRIMARY KEY,
              email         TEXT NOT NULL UNIQUE,
              name          TEXT,
              password_hash TEXT NOT NULL,
              role          TEXT DEFAULT 'user',
              is_active     BOOLEAN DEFAULT TRUE,
              created_at    TIMESTAMPTZ DEFAULT now()
            );
        """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_app_user_email ON eta.app_user(lower(email));"))

        # Seed admin (usa pbkdf2_sha256)
        admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
        admin_name = os.getenv("ADMIN_NAME", "Admin")
        admin_pwd = os.getenv("ADMIN_PASSWORD", "").strip()

        if admin_email and admin_pwd and HAVE_PASSLIB:
            exists = conn.execute(
                text("SELECT 1 FROM eta.app_user WHERE lower(email)=:e LIMIT 1;"), {"e": admin_email}
            ).fetchone()
            if not exists:
                pwd_hash = hash_password(admin_pwd)
                conn.execute(
                    text(
                        """INSERT INTO eta.app_user(email, name, password_hash, role, is_active)
                            VALUES (:e, :n, :p, 'admin', TRUE);"""
                    ),
                    {"e": admin_email, "n": admin_name, "p": pwd_hash},
                )


# ------------------------- Auth helpers -------------------------
def auth_get_user(email: str):
    engine = create_engine(DB_URL, pool_pre_ping=True)
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """SELECT id, email, name, password_hash, role, is_active
                    FROM eta.app_user WHERE lower(email)=:e;"""
            ),
            {"e": email.lower().strip()},
        ).fetchone()
        return dict(row._mapping) if row else None


def auth_verify_password(plain: str, hashed: str) -> bool:
    if not HAVE_PASSLIB:
        raise RuntimeError("Dependência faltando: instale 'passlib'")
    return verify_password(plain, hashed)


def require_login():
    if "user" in st.session_state and st.session_state["user"] is not None:
        return st.session_state["user"]

    st.sidebar.header("Login")
    with st.sidebar.form("login_form", clear_on_submit=False):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Senha", type="password", key="login_password")
        remember = st.checkbox("Manter conectado", value=True)
        submitted = st.form_submit_button("Entrar")

    if submitted:
        try:
            u = auth_get_user(email)
            if not u or not u.get("is_active", True):
                st.sidebar.error("Usuário não encontrado ou inativo.")
                st.stop()
            if not auth_verify_password(password, u["password_hash"]):
                st.sidebar.error("Senha inválida.")
                st.stop()
            st.session_state["user"] = {
                "id": u["id"],
                "email": u["email"],
                "name": u.get("name") or u["email"],
                "role": u.get("role", "user"),
                "remember": remember,
            }
            st.sidebar.success(f"Bem-vindo, {st.session_state['user']['name']}!")
        except Exception as e:
            st.sidebar.error(f"Falha no login: {e}")
            st.stop()

    st.info("🔒 Faça login para acessar o sistema.")
    st.stop()


def logout_button():
    with st.sidebar:
        if st.button("Sair", use_container_width=True):
            st.session_state["user"] = None
            st.experimental_rerun()


# ------------------------- Utils/Pandas -------------------------
def _sanitize(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df["ts"] = (
        pd.to_datetime(df["ts"], utc=True, errors="coerce")
        .dt.tz_convert(LOCAL_TZ)
        .dt.tz_localize(None)
    )
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna(subset=["ts", "value"]).sort_values("ts")


@st.cache_data(ttl=5, show_spinner=False)
def load_from_db(db_url: str, start_dt: datetime) -> pd.DataFrame:
    if not HAVE_SQLA:
        raise RuntimeError("SQLAlchemy não está instalado.")
    engine = create_engine(db_url, pool_pre_ping=True)
    with engine.connect() as conn:
        q = text(
            """
            SELECT m.ts, s.tag, m.value, s.unit, m.quality, m.meta
            FROM eta.measurement m
            JOIN eta.sensor s ON s.id = m.sensor_id
            WHERE m.ts >= :start_dt
            ORDER BY m.ts ASC;
        """
        )
        res = conn.execute(q, {"start_dt": start_dt})
        df = pd.DataFrame(res.fetchall(), columns=["ts", "tag", "value", "unit", "quality", "meta"])
    return _sanitize(df)


def fetch_period(db_url: str, start_utc: datetime, end_utc: datetime) -> pd.DataFrame:
    engine = create_engine(db_url, pool_pre_ping=True)
    with engine.connect() as conn:
        q = text(
            """
            SELECT m.ts, s.tag, m.value, s.unit, m.quality, m.meta
            FROM eta.measurement m
            JOIN eta.sensor s ON s.id = m.sensor_id
            WHERE m.ts >= :start_dt AND m.ts < :end_dt
            ORDER BY m.ts ASC;
        """
        )
        res = conn.execute(q, {"start_dt": start_utc, "end_dt": end_utc})
        df = pd.DataFrame(res.fetchall(), columns=["ts", "tag", "value", "unit", "quality", "meta"])
    return _sanitize(df)


def to_utc(ts_local: pd.Timestamp) -> datetime:
    return ts_local.tz_convert("UTC").to_pydatetime()


def compute_range(choice: str, custom_range: tuple[date, date] | None):
    now_local = pd.Timestamp.now(tz=LOCAL_TZ)
    if choice == "Últimos 30 dias":
        start_local, end_local, label = now_local - pd.Timedelta(days=30), now_local, "ultimos_30_dias"
    elif choice == "Últimos 7 dias":
        start_local, end_local, label = now_local - pd.Timedelta(days=7), now_local, "ultimos_7_dias"
    elif choice == "Último 1 dia":
        start_local, end_local, label = now_local - pd.Timedelta(days=1), now_local, "ultimo_1_dia"
    else:
        assert custom_range and len(custom_range) == 2
        d_ini, d_fim = custom_range
        start_local = pd.Timestamp(d_ini, tz=LOCAL_TZ)
        end_local = pd.Timestamp(d_fim + timedelta(days=1), tz=LOCAL_TZ)
        label = f"{d_ini:%Y-%m-%d}_a_{d_fim:%Y-%m-%d}"
    return to_utc(start_local), to_utc(end_local), label


def build_excel_report(
    df: pd.DataFrame,
    label_periodo: str,
    start_utc: datetime,
    end_utc: datetime,
) -> bytes:
    def _autosize(ws, data: pd.DataFrame):
        for i, col in enumerate(data.columns):
            try:
                max_len = max(len(str(col)), *(data[col].astype(str).map(len).tolist()))
            except Exception:
                max_len = 18
            ws.set_column(i, i, min(max_len + 2, 40))

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter", datetime_format="yyyy-mm-dd HH:MM:SS") as xw:
        if df.empty:
            vazio = pd.DataFrame({"aviso": [f"Sem dados para {label_periodo}."]})
            vazio.to_excel(xw, sheet_name="Resumo", index=False)
            _autosize(xw.sheets["Resumo"], vazio)
            return buf.getvalue()

        df["data"] = df["ts"].dt.date
        df["hora"] = df["ts"].dt.floor("h")

        last = df.sort_values("ts").groupby("tag", as_index=False).tail(1)
        resumo = (
            df.groupby("tag")
            .agg(
                **{
                    "Qtd de Leitura": ("value", "count"),
                    "media": ("value", "mean"),
                    "minimo": ("value", "min"),
                    "maximo": ("value", "max"),
                }
            )
            .reset_index()
            .merge(last[["tag", "value", "ts", "unit"]], on="tag", how="left")
            .rename(columns={"value": "ultimo_valor", "ts": "ultimo_ts", "unit": "unidade"})
        )

        diario = (
            df.groupby(["tag", "data"], as_index=False)
            .agg(
                **{
                    "Qtd de Leitura": ("value", "count"),
                    "media": ("value", "mean"),
                    "minimo": ("value", "min"),
                    "maximo": ("value", "max"),
                }
            )
            .sort_values(["tag", "data"])
        )

        horario = (
            df.groupby(["tag", "hora"], as_index=False)
            .agg(
                **{
                    "Qtd de Leitura": ("value", "count"),
                    "media": ("value", "mean"),
                    "minimo": ("value", "min"),
                    "maximo": ("value", "max"),
                }
            )
            .sort_values(["tag", "hora"])
        )

        bruto = df[["ts", "tag", "unit", "value", "quality", "meta"]].sort_values("ts")

        seconds = max(0, int((end_utc - start_utc).total_seconds()))
        esperado = max(1, seconds // FEED_INTERVAL)
        resumo["completude_%"] = (resumo["Qtd de Leitura"] / esperado * 100).clip(upper=100).round(1)

        resumo.to_excel(xw, sheet_name="Resumo", index=False)
        diario.to_excel(xw, sheet_name="Diario", index=False)
        horario.to_excel(xw, sheet_name="Horario", index=False)
        bruto.to_excel(xw, sheet_name="Bruto", index=False)

        for name, data in [("Resumo", resumo), ("Diario", diario), ("Horario", horario), ("Bruto", bruto)]:
            ws = xw.sheets[name]
            ws.freeze_panes(1, 1)
            _autosize(ws, data)

    return buf.getvalue()


# ------------------------- Visual -------------------------
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
            st.metric(
                label=label,
                value=f"{row.value:.3f}",
                help=f"Última leitura em {row.ts:%d/%m/%y %H:%M:%S}",
            )


def _plotly_config():
    return {
        "displaylogo": False,
        "responsive": True,
        "modeBarButtonsToRemove": [
            "toggleSpikelines",
            "autoScale2d",
            "hoverCompareCartesian",
            "orbitRotation",
            "tableRotation",
            "lasso2d",
            "select2d",
        ],
    }


def charts_split(df: pd.DataFrame, tags: list[str], limits: dict[str, float] | None = None):
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
        unit = (
            dft["unit"].dropna().iloc[0]
            if "unit" in dft and not dft["unit"].isna().all()
            else ""
        )
        last = dft.iloc[-1]
        titulo_hora = f"{last['ts']:%d/%m/%y %H:%M:%S}"
        title = (
            f"{tag} ({unit}) • Último: {last['value']:.3f} às {titulo_hora}"
            if unit
            else f"{tag} • Último: {last['value']:.3f} às {titulo_hora}"
        )
        y_min, y_max = float(dft["value"].min()), float(dft["value"].max())
        pad = (y_max - y_min) * 0.08 if y_max > y_min else 1.0
        y_range = [y_min - pad, y_max + pad]
        fig = px.line(
            dft,
            x="ts",
            y="value",
            title=title,
            labels={"ts": "Tempo", "value": f"Valor ({unit})" if unit else "Valor"},
        )
        fig.update_traces(
            mode="lines+markers",
            marker=dict(size=4),
            hovertemplate="<b>%{y:.4f}</b><br>%{x}<extra></extra>",
            showlegend=False,
        )
        fig.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=54, b=10),
            xaxis=dict(title=None, showgrid=True),
            yaxis=dict(range=y_range, showgrid=True, title=f"{unit}" if unit else "valor"),
        )
        if limits and tag in limits:
            fig.add_hline(
                y=float(limits[tag]),
                line_dash="dot",
                annotation_text=f"Limite {limits[tag]:.2f}",
                annotation_position="top left",
            )
        with cols[i % ncols]:
            st.plotly_chart(fig, use_container_width=True, config=_plotly_config())


def format_alert_table(df_alert: pd.DataFrame) -> pd.DataFrame:
    if df_alert.empty:
        return df_alert
    return (
        df_alert.assign(timestamp=df_alert["ts"].dt.strftime("%d/%m/%y %H:%M:%S"))
        .rename(columns={"value": "valor"})
        .loc[:, ["timestamp", "valor"]]
        .sort_values("timestamp", ascending=False)
    )


def layout_alertas(df: pd.DataFrame, limits: dict[str, float]):
    st.subheader("Alertas")
    tags_existentes = [t for t in TAGS_PADRAO if t in df["tag"].unique()]
    if not tags_existentes:
        st.info("Sem leituras no período visualizado.")
        return

    tabs = st.tabs(tags_existentes)

    # cooldown em minutos entre notificações por tag (email/whatsapp)
    cooldown_min = int(os.getenv("ALERT_EMAIL_COOLDOWN_MIN", "10"))

    for tab, tag in zip(tabs, tags_existentes):
        with tab:
            dft = df[df["tag"] == tag].sort_values("ts")
            if dft.empty:
                st.info("Sem dados para a tag no período.")
                continue

            unit = (
                dft["unit"].dropna().iloc[0]
                if "unit" in dft and not dft["unit"].isna().all()
                else ""
            )
            last_val = float(dft["value"].iloc[-1])
            last_ts = dft["ts"].iloc[-1]

            st.metric(
                f"{tag} ({unit})" if unit else tag,
                f"{last_val:.3f}",
                help=f"Última leitura em {last_ts:%d/%m/%y %H:%M:%S}",
            )

            limite = limits.get(tag, None)
            if limite is not None:
                if last_val > limite:
                    st.error(
                        f"⚠️ Alerta: valor atual **{last_val:.2f}** acima do limite **{limite:.2f}**."
                    )

                    # --------- ENVIO DE NOTIFICAÇÕES COM COOLDOWN ---------
                    now = datetime.utcnow()
                    state_key = f"last_alert_sent_{tag}"
                    last_sent = st.session_state.get(state_key)

                    deve_enviar = (
                        last_sent is None
                        or (now - last_sent).total_seconds() > cooldown_min * 60
                    )

                    if deve_enviar:
                        valor_str = f"{last_val:.3f} {unit}" if unit else f"{last_val:.3f}"
                        ts_str = f"{last_ts:%d/%m/%y %H:%M:%S}"
                        msg_extra = (
                            f"Tag {tag} acima do limite {limite:.2f}. "
                            f"Última leitura em {ts_str}."
                        )

                        email_ok = False
                        wpp_ok = False

                        # E-mail
                        try:
                            email_ok = enviar_alerta_para_destinatarios_padrao(
                                equipamento=tag,
                                valor_kpi=valor_str,
                                mensagem_extra=msg_extra,
                            )
                        except Exception as e:
                            st.warning(f"Falha ao tentar enviar e-mail de alerta: {e}")

                        # WhatsApp (se módulo estiver disponível)
                        if HAVE_WPP:
                            try:
                                wpp_ok = enviar_alerta_whatsapp_para_destinatarios_padrao(
                                    equipamento=tag,
                                    valor_kpi=valor_str,
                                    limite=limite,
                                    timestamp=ts_str,
                                )
                            except Exception as e:
                                st.warning(f"Falha ao tentar enviar alerta via WhatsApp: {e}")

                        if email_ok or wpp_ok:
                            st.session_state[state_key] = now  # grava cooldown
                            if email_ok and wpp_ok:
                                st.info("✉️📲 Alerta enviado por e-mail e WhatsApp aos responsáveis.")
                            elif email_ok:
                                st.info("✉️ Alerta enviado por e-mail aos responsáveis.")
                            elif wpp_ok:
                                st.info("📲 Alerta enviado por WhatsApp aos responsáveis.")
                        else:
                            st.warning("Não foi possível enviar o alerta (e-mail/WhatsApp).")
                    else:
                        st.caption(
                            f"Alerta já enviado recentemente para esta tag "
                            f"(cooldown {cooldown_min} min)."
                        )
                    # -------------------------------------------------
                else:
                    st.success(
                        f"✅ Valor atual **{last_val:.2f}** dentro do limite (**≤ {limite:.2f}**)."
                    )

                acima = dft[dft["value"] > limite]
                if not acima.empty:
                    st.warning(
                        f"Ocorrências acima do limite no período: **{len(acima)}**"
                    )
                    st.dataframe(
                        format_alert_table(acima), use_container_width=True
                    )
                else:
                    st.info("Nenhuma ocorrência acima do limite no período.")


def layout(df: pd.DataFrame, limits: dict[str, float], user: dict):
    with st.sidebar:
        st.caption(f"👤 {user['name']} • {user['email']} • role: {user['role']}")
    layout_alertas(df, limits)
    st.divider()
    st.subheader("KPIs (últimas leituras por tag)")
    make_kpi_cards(df)
    st.divider()
    st.subheader("Séries temporais")
    tags_sel = st.multiselect(
        "Selecione as tags para plotar", TAGS_PADRAO, default=TAGS_PADRAO
    )
    charts_split(df, tags_sel, limits=limits)


# ------------------------- Sidebar / Run -------------------------
st.sidebar.header("Banco de Dados")

# Prepara DB + seed admin
try:
    ensure_db(DB_URL)
except Exception as e:
    st.error(f"Falha ao preparar o banco: {e}")
    st.stop()

# Exige login
user = require_login()
logout_button()

if USING_DATABASE_URL:
    st.sidebar.success("Usando DATABASE_URL (Render/Produção)")
else:
    st.sidebar.warning("Usando Conexão CLP/NodeRed/DBLocal")

date_range = st.sidebar.selectbox(
    "Período (viewer)",
    ["Últimos 15 min", "Últimas 2 h", "Últimos 24 h", "Últimos 7 dias"],
    index=2,
)
if date_range.startswith("Últimos 15"):
    delta = timedelta(minutes=15)
elif date_range.startswith("Últimas 2"):
    delta = timedelta(hours=2)
elif date_range.startswith("Últimos 24"):
    delta = timedelta(hours=24)
else:
    delta = timedelta(days=7)
start = datetime.utcnow() - delta

# Alertas por tag
st.sidebar.markdown("---")
st.sidebar.subheader("Alertas (limites por tag)")
limits: dict[str, float] = {}
for tag in TAGS_PADRAO:
    default = ALERT_DEFAULTS.get(tag, 0.0)
    limits[tag] = st.sidebar.number_input(
        f"Limite • {tag}",
        value=float(default),
        step=0.1,
        format="%.2f",
        help=f"Dispara alerta quando {tag} > limite",
    )

st.sidebar.markdown("---")
st.sidebar.subheader("Relatório (Excel)")
rep_choice = st.sidebar.radio(
    "Período do relatório",
    ["Últimos 30 dias", "Últimos 7 dias", "Último 1 dia", "Período específico"],
    index=0,
)
custom_range = None
if rep_choice == "Período específico":
    custom_range = st.sidebar.date_input(
        "Escolha o intervalo",
        value=(date.today() - timedelta(days=7), date.today()),
        format="DD/MM/YYYY",
    )
gen = st.sidebar.button("Gerar Excel")

refresh_s = st.sidebar.number_input("Atualização (s)", 1, 120, 60, 1)
st.caption(f"Fuso: {LOCAL_TZ}  •  Auto-refresh: {int(refresh_s)}s")
st_autorefresh(interval=int(refresh_s * 1000), key="db_refresh")

try:
    df_view = load_from_db(DB_URL, start)
    if df_view.empty:
        st.warning(
            "Sem dados no intervalo. Publique no worker/feeder ou amplie o período."
        )
    else:
        layout(df_view, limits=limits, user=user)

    if gen:
        start_utc, end_utc, label = compute_range(rep_choice, custom_range)
        df_period = fetch_period(DB_URL, start_utc, end_utc)
        xlsx_bytes = build_excel_report(df_period, label, start_utc, end_utc)
        fname = f"relatorio_ETA_{label}.xlsx"
        st.sidebar.success("Relatório pronto.")
        st.sidebar.download_button(
            "Baixar Excel",
            data=xlsx_bytes,
            file_name=fname,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
except Exception as e:
    st.error(f"Falha ao conectar/carregar: {e}")

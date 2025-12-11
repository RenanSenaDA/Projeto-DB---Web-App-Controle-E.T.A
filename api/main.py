import os
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, field_validator
import re
from passlib.hash import pbkdf2_sha256, bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from dotenv import load_dotenv, find_dotenv
import io
import pandas as pd


# --- Env ---
load_dotenv(find_dotenv())
for extra in [
    os.path.join(os.getcwd(), ".env"),
]:
    if os.path.exists(extra):
        load_dotenv(extra, override=False)

# Converte URL para formato compatível com SQLAlchemy/psycopg v3
def to_sqlalchemy_url(url: str) -> str:
    if not url:
        return url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    # Normalize any driver to psycopg (v3)
    if url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and "postgresql+psycopg://" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url

# Monta URL do banco a partir de envs; fallback para defaults locais
def get_db_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return to_sqlalchemy_url(url)
    host = os.getenv("PGHOST", os.getenv("DB_HOST", "localhost"))
    port = os.getenv("PGPORT", os.getenv("DB_PORT", "5432"))
    user = os.getenv("PGUSER", os.getenv("POSTGRES_USER", "postgres"))
    pwd = os.getenv("PGPASSWORD", os.getenv("POSTGRES_PASSWORD", "postgres"))
    db = os.getenv("PGDATABASE", os.getenv("POSTGRES_DB", "eta"))
    return f"postgresql+psycopg://{user}:{pwd}@{host}:{port}/{db}"

# Cria Engine SQLAlchemy com pool_pre_ping para manter conexões válidas
def get_engine() -> Engine:
    return create_engine(get_db_url(), pool_pre_ping=True)


# --- Auth helpers ---
# Gera hash de senha com pbkdf2
def hash_password(plain: str) -> str:
    return pbkdf2_sha256.hash(plain)


# Verifica senha contra hash pbkdf2/bcrypt
def verify_password(plain: str, hashed: str) -> bool:
    try:
        if hashed.startswith("$pbkdf2-sha256$"):
            return pbkdf2_sha256.verify(plain, hashed)
        return bcrypt.verify(plain, hashed)
    except Exception:
        return False


# --- Models ---
class LoginIn(BaseModel):
    """Payload de login (email/senha)."""
    email: EmailStr
    password: str


class RegisterIn(BaseModel):
    """Payload de registro de usuário com validações."""
    name: str
    email: EmailStr
    password: str

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        v = (v or "").strip()
        if len(v) < 2:
            raise ValueError("Nome muito curto")
        return v

    @field_validator("password")
    @classmethod
    def _validate_password(cls, v: str) -> str:
        if not v or len(v) < 8:
            raise ValueError("Senha fraca: mínimo 8 caracteres")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Senha fraca: incluir letra maiúscula")
        if not re.search(r"[a-z]", v):
            raise ValueError("Senha fraca: incluir letra minúscula")
        if not re.search(r"\d", v):
            raise ValueError("Senha fraca: incluir número")
        if not re.search(r"[^A-Za-z0-9]", v):
            raise ValueError("Senha fraca: incluir símbolo")
        return v


class SensorOut(BaseModel):
    """Modelo de saída de sensor (id/tag/unidade)."""
    id: int
    tag: str
    unit: Optional[str] = None


class MeasurementPoint(BaseModel):
    """Ponto de medição com timestamp, valor e unidade."""
    ts: datetime
    tag: str
    value: float
    unit: Optional[str] = None


class LimitsOut(BaseModel):
    """Estrutura de limites atuais por tag."""
    limits: Dict[str, float]


class DashboardKPI(BaseModel):
    """Representa um KPI no dashboard (metadados e categoria)."""
    id: str
    label: str
    value: Optional[float]
    unit: Optional[str]
    limit: Optional[float] = None
    category: str = "default"
    updated_at: datetime


class DashboardOut(BaseModel):
    """Envelope do dashboard com meta e dados por estação."""
    meta: Dict[str, str]
    data: Dict[str, Dict[str, List[DashboardKPI]]]


app = FastAPI(title="Aqualink API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def categorize(tag: str) -> str:
    """Infere categoria a partir do prefixo da tag."""
    tl = tag.lower()
    if tl.startswith("qualidade/"):
        return "qualidade_da_agua"
    if tl.startswith("decantacao/") or tl.startswith("bombeamento/") or tl.startswith("pressao/") or tl.startswith("nivel/"):
        return "operacional"
    return "default"

LOCAL_TZ = os.getenv("LOCAL_TZ", os.getenv("TZ", "America/Fortaleza"))
FEED_INTERVAL = int(os.getenv("FEED_INTERVAL", "5"))

def _sanitize_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza colunas ts/value e ordena; remove inválidos."""
    if df.empty:
        return df
    df["ts"] = (
        pd.to_datetime(df["ts"], utc=True, errors="coerce").dt.tz_convert(LOCAL_TZ).dt.tz_localize(None)
    )
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["ts", "value"]) .sort_values("ts")
    return df


# --- Auth endpoints ---
@app.post("/auth/login")
def auth_login(payload: LoginIn):
    """Autentica usuário por email/senha; retorna token dummy."""
    eng = get_engine()
    with eng.connect() as conn:
        row = conn.execute(
            text(
                """SELECT id, email, name, password_hash, role
                    FROM eta.app_user WHERE lower(email)=:e;"""
            ),
            {"e": payload.email.lower().strip()},
        ).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        ok = verify_password(payload.password, row._mapping["password_hash"])
        if not ok:
            raise HTTPException(status_code=401, detail="Senha inválida")
        token = f"dummy-{row._mapping['id']}-{int(datetime.utcnow().timestamp())}"
        return {"token": token, "user": {"id": row._mapping["id"], "email": row._mapping["email"], "name": row._mapping.get("name") or row._mapping["email"], "role": row._mapping.get("role", "user")}}


@app.post("/auth/register")
def auth_register(payload: RegisterIn):
    """Registra novo usuário; falha se email existente."""
    eng = get_engine()
    with eng.begin() as conn:
        exists = conn.execute(text("SELECT 1 FROM eta.app_user WHERE lower(email)=:e LIMIT 1;"), {"e": payload.email.lower().strip()}).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="Email já cadastrado")
        pwd_hash = hash_password(payload.password)
        conn.execute(
            text("""INSERT INTO eta.app_user(email, name, password_hash, role, is_active)
                    VALUES (:e, :n, :p, 'user', TRUE);"""),
            {"e": payload.email.lower().strip(), "n": payload.name.strip(), "p": pwd_hash},
        )
    return {"ok": True}


# --- Sensors ---
@app.get("/sensors", response_model=List[SensorOut])
def list_sensors():
    """Lista sensores disponíveis ordenados por id."""
    eng = get_engine()
    with eng.connect() as conn:
        rows = conn.execute(text("SELECT id, tag, unit FROM eta.sensor ORDER BY id; ")).fetchall()
        return [{"id": r._mapping["id"], "tag": r._mapping["tag"], "unit": r._mapping["unit"]} for r in rows]


# --- Measurements ---
@app.get("/measurements/latest", response_model=List[MeasurementPoint])
def latest_by_sensor():
    """Retorna última medição de cada sensor com join em sensor."""
    eng = get_engine()
    with eng.connect() as conn:
        q = text(
            """
            SELECT m.ts, s.tag, m.value, s.unit
            FROM eta.measurement m
            JOIN eta.sensor s ON s.id = m.sensor_id
            JOIN (
                SELECT sensor_id, max(ts) AS ts
                FROM eta.measurement
                GROUP BY sensor_id
            ) last ON last.sensor_id = m.sensor_id AND last.ts = m.ts
            ORDER BY s.tag;
            """
        )
        rows = conn.execute(q).fetchall()
        return [{"ts": r._mapping["ts"], "tag": r._mapping["tag"], "value": float(r._mapping["value"]), "unit": r._mapping.get("unit") } for r in rows]


@app.get("/measurements/series")
def series(tags: str, minutes: int = 60):
    """Busca séries para tags em janela de tempo (minutos)."""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    if not tag_list:
        return {}
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(minutes=minutes)
    eng = get_engine()
    with eng.connect() as conn:
        q = text(
            """
            SELECT m.ts, s.tag, m.value, s.unit
            FROM eta.measurement m
            JOIN eta.sensor s ON s.id = m.sensor_id
            WHERE m.ts >= :start_dt AND m.ts <= :end_dt AND s.tag = ANY(:tags)
            ORDER BY s.tag, m.ts ASC;
            """
        )
        rows = conn.execute(q, {"start_dt": start_dt, "end_dt": end_dt, "tags": tag_list}).fetchall()
    data: Dict[str, List[Dict]] = {}
    for r in rows:
        tag = r._mapping["tag"]
        data.setdefault(tag, []).append({
            "ts": r._mapping["ts"],
            "value": float(r._mapping["value"]),
            "unit": r._mapping.get("unit"),
        })
    return data


# --- Limits ---
@app.get("/limits", response_model=LimitsOut)
def get_limits():
    """Obtém limites configurados para cada tag."""
    eng = get_engine()
    with eng.connect() as conn:
        rows = conn.execute(text("SELECT tag, limite FROM eta.config_limites; ")).fetchall()
    limits: Dict[str, float] = {}
    for r in rows:
        try:
            limits[r._mapping["tag"]] = float(r._mapping["limite"])
        except Exception:
            continue
    return {"limits": limits}


class LimitsIn(BaseModel):
    """Entrada para atualizar limites por tag."""
    limits: Dict[str, float]


@app.put("/limits")
def put_limits(payload: LimitsIn):
    """Insere/atualiza limites; upsert por tag com conflito."""
    eng = get_engine()
    with eng.begin() as conn:
        for tag, lim in payload.limits.items():
            conn.execute(text(
                """
                INSERT INTO eta.config_limites(tag, limite)
                VALUES (:tag, :limite)
                ON CONFLICT(tag) DO UPDATE SET limite=EXCLUDED.limite, updated_at=now();
                """
            ), {"tag": tag, "limite": float(lim)})
    return {"ok": True}


# --- Alarms status ---
@app.get("/alarms/status")
def alarms_status():
    eng = get_engine()
    with eng.connect() as conn:
        row = conn.execute(text("SELECT alarms_enabled FROM config_sistema WHERE id=1;")).fetchone()
    return {"alarms_enabled": bool(row._mapping["alarms_enabled"]) if row else True}


class AlarmsIn(BaseModel):
    alarms_enabled: bool


@app.put("/alarms/status")
def set_alarms(payload: AlarmsIn):
    eng = get_engine()
    with eng.begin() as conn:
        conn.execute(text("UPDATE config_sistema SET alarms_enabled=:v, updated_at=now() WHERE id=1;"), {"v": bool(payload.alarms_enabled)})
    return {"ok": True}


# --- Dashboard ---
@app.get("/dashboard", response_model=DashboardOut)
def dashboard():
    eng = get_engine()
    with eng.connect() as conn:
        last = conn.execute(text(
            """
            SELECT m.ts, s.tag, m.value, s.unit
            FROM eta.measurement m
            JOIN eta.sensor s ON s.id = m.sensor_id
            JOIN (
                SELECT sensor_id, max(ts) AS ts
                FROM eta.measurement
                GROUP BY sensor_id
            ) last ON last.sensor_id = m.sensor_id AND last.ts = m.ts
            ORDER BY s.tag;
            """
        )).fetchall()
        lim_rows = conn.execute(text("SELECT tag, limite FROM eta.config_limites;")).fetchall()

    limits: Dict[str, float] = {r._mapping["tag"]: float(r._mapping["limite"]) for r in lim_rows}
    eta_kpis: List[DashboardKPI] = []
    for r in last:
        tag = r._mapping["tag"]
        val = float(r._mapping["value"]) if r._mapping["value"] is not None else None
        unit = r._mapping.get("unit")
        eta_kpis.append(DashboardKPI(
            id=tag.replace("/", "_"),
            label=tag if not unit else f"{tag} ({unit})",
            value=val,
            unit=unit,
            limit=limits.get(tag),
            category=categorize(tag),
            updated_at=r._mapping["ts"],
        ))

    data = {
        "eta": {"kpis": eta_kpis},
        "ultrafiltracao": {"kpis": []},
        "carvao": {"kpis": []},
    }
    return {"meta": {"timestamp": datetime.utcnow().isoformat(), "status": "online"}, "data": data}


# --- Reports ---
@app.get("/reports/excel")
def report_excel(period: str = "ultimos_7_dias"):
    now = datetime.utcnow()
    if period == "ultimos_30_dias":
        start = now - timedelta(days=30)
    elif period == "ultimos_7_dias":
        start = now - timedelta(days=7)
    elif period == "ultimo_1_dia":
        start = now - timedelta(days=1)
    else:
        start = now - timedelta(days=7)

    eng = get_engine()
    with eng.connect() as conn:
        q = text(
            """
            SELECT m.ts, s.tag, m.value, s.unit, m.quality, m.meta
            FROM eta.measurement m
            JOIN eta.sensor s ON s.id = m.sensor_id
            WHERE m.ts >= :start_dt AND m.ts < :end_dt
            ORDER BY m.ts ASC;
            """
        )
        rows = conn.execute(q, {"start_dt": start, "end_dt": now}).fetchall()
        df = pd.DataFrame(rows, columns=["ts", "tag", "value", "unit", "quality", "meta"]) if rows else pd.DataFrame(columns=["ts","tag","value","unit","quality","meta"])

    df = _sanitize_df(df)

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
            vazio = pd.DataFrame({"aviso": [f"Sem dados para {period}."]})
            vazio.to_excel(xw, sheet_name="Resumo", index=False)
            _autosize(xw.sheets["Resumo"], vazio)
        else:
            df["data"] = df["ts"].dt.date
            df["hora"] = df["ts"].dt.floor("h")

            last = df.sort_values("ts").groupby("tag", as_index=False).tail(1)
            resumo = (
                df.groupby("tag")
                .agg(**{"Qtd de Leitura": ("value", "count"), "media": ("value", "mean"), "minimo": ("value", "min"), "maximo": ("value", "max")})
                .reset_index()
                .merge(last[["tag", "value", "ts", "unit"]], on="tag", how="left")
                .rename(columns={"value": "ultimo_valor", "ts": "ultimo_ts", "unit": "unidade"})
            )

            seconds = max(0, int((now - start).total_seconds()))
            esperado = max(1, seconds // FEED_INTERVAL)
            resumo["completude_%"] = (resumo["Qtd de Leitura"] / esperado * 100).clip(upper=100).round(1)

            diario = (
                df.groupby(["tag", "data"], as_index=False)
                .agg(**{"Qtd de Leitura": ("value", "count"), "media": ("value", "mean"), "minimo": ("value", "min"), "maximo": ("value", "max")})
                .sort_values(["tag", "data"])
            )

            horario = (
                df.groupby(["tag", "hora"], as_index=False)
                .agg(**{"Qtd de Leitura": ("value", "count"), "media": ("value", "mean"), "minimo": ("value", "min"), "maximo": ("value", "max")})
                .sort_values(["tag", "hora"])
            )

            bruto = df[["ts", "tag", "unit", "value", "quality", "meta"]].sort_values("ts")

            resumo.to_excel(xw, sheet_name="Resumo", index=False)
            diario.to_excel(xw, sheet_name="Diario", index=False)
            horario.to_excel(xw, sheet_name="Horario", index=False)
            bruto.to_excel(xw, sheet_name="Bruto", index=False)

            for name, data_tbl in [("Resumo", resumo), ("Diario", diario), ("Horario", horario), ("Bruto", bruto)]:
                ws = xw.sheets[name]
                ws.freeze_panes(1, 1)
                _autosize(ws, data_tbl)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename=relatorio_{period}.xlsx"})


@app.get("/reports/excel-range")
def report_excel_range(start: date, end: date, tags: Optional[str] = None):
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end + timedelta(days=1), datetime.min.time())
    tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
    eng = get_engine()
    with eng.connect() as conn:
        if tag_list:
            q = text(
                """
                SELECT m.ts, s.tag, m.value, s.unit, m.quality, m.meta
                FROM eta.measurement m
                JOIN eta.sensor s ON s.id = m.sensor_id
                WHERE m.ts >= :start_dt AND m.ts < :end_dt AND s.tag = ANY(:tags)
                ORDER BY m.ts ASC;
                """
            )
            rows = conn.execute(q, {"start_dt": start_dt, "end_dt": end_dt, "tags": tag_list}).fetchall()
        else:
            q = text(
                """
                SELECT m.ts, s.tag, m.value, s.unit, m.quality, m.meta
                FROM eta.measurement m
                JOIN eta.sensor s ON s.id = m.sensor_id
                WHERE m.ts >= :start_dt AND m.ts < :end_dt
                ORDER BY m.ts ASC;
                """
            )
            rows = conn.execute(q, {"start_dt": start_dt, "end_dt": end_dt}).fetchall()
        df = pd.DataFrame(rows, columns=["ts", "tag", "value", "unit", "quality", "meta"]) if rows else pd.DataFrame(columns=["ts","tag","value","unit","quality","meta"])

    df = _sanitize_df(df)

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
            vazio = pd.DataFrame({"aviso": [f"Sem dados para {start} a {end}."]})
            vazio.to_excel(xw, sheet_name="Resumo", index=False)
            _autosize(xw.sheets["Resumo"], vazio)
        else:
            df["data"] = df["ts"].dt.date
            df["hora"] = df["ts"].dt.floor("h")

            last = df.sort_values("ts").groupby("tag", as_index=False).tail(1)
            resumo = (
                df.groupby("tag")
                .agg(**{"Qtd de Leitura": ("value", "count"), "media": ("value", "mean"), "minimo": ("value", "min"), "maximo": ("value", "max")})
                .reset_index()
                .merge(last[["tag", "value", "ts", "unit"]], on="tag", how="left")
                .rename(columns={"value": "ultimo_valor", "ts": "ultimo_ts", "unit": "unidade"})
            )

            seconds = max(0, int((end_dt - start_dt).total_seconds()))
            esperado = max(1, seconds // FEED_INTERVAL)
            resumo["completude_%"] = (resumo["Qtd de Leitura"] / esperado * 100).clip(upper=100).round(1)

            diario = (
                df.groupby(["tag", "data"], as_index=False)
                .agg(**{"Qtd de Leitura": ("value", "count"), "media": ("value", "mean"), "minimo": ("value", "min"), "maximo": ("value", "max")})
                .sort_values(["tag", "data"])
            )

            horario = (
                df.groupby(["tag", "hora"], as_index=False)
                .agg(**{"Qtd de Leitura": ("value", "count"), "media": ("value", "mean"), "minimo": ("value", "min"), "maximo": ("value", "max")})
                .sort_values(["tag", "hora"])
            )

            bruto = df[["ts", "tag", "unit", "value", "quality", "meta"]].sort_values("ts")

            resumo.to_excel(xw, sheet_name="Resumo", index=False)
            diario.to_excel(xw, sheet_name="Diario", index=False)
            horario.to_excel(xw, sheet_name="Horario", index=False)
            bruto.to_excel(xw, sheet_name="Bruto", index=False)

            for name, data_tbl in [("Resumo", resumo), ("Diario", diario), ("Horario", horario), ("Bruto", bruto)]:
                ws = xw.sheets[name]
                ws.freeze_panes(1, 1)
                _autosize(ws, data_tbl)
    buf.seek(0)
    fname = f"relatorio_{start}_{end}.xlsx"
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename={fname}"})

@app.get("/")
def root():
    return {"ok": True, "service": "Aqualink API"}

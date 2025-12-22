import os
import re
import io
import secrets
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any

import pandas as pd
from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from passlib.hash import pbkdf2_sha256, bcrypt
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


# --- Env ---
load_dotenv(find_dotenv())
for extra in [os.path.join(os.getcwd(), ".env")]:
    if os.path.exists(extra):
        load_dotenv(extra, override=False)


def to_sqlalchemy_url(url: str) -> str:
    """Converte URL para formato compatível com SQLAlchemy/psycopg v3."""
    if not url:
        return url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and "postgresql+psycopg://" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def get_db_url() -> str:
    """Monta URL do banco a partir de envs; fallback para defaults locais."""
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return to_sqlalchemy_url(url)

    host = os.getenv("PGHOST", os.getenv("DB_HOST", "localhost"))
    port = os.getenv("PGPORT", os.getenv("DB_PORT", "5432"))
    user = os.getenv("PGUSER", os.getenv("POSTGRES_USER", "postgres"))
    pwd = os.getenv("PGPASSWORD", os.getenv("POSTGRES_PASSWORD", "postgres"))
    db = os.getenv("PGDATABASE", os.getenv("POSTGRES_DB", "eta"))
    return f"postgresql+psycopg://{user}:{pwd}@{host}:{port}/{db}"


def get_engine() -> Engine:
    """Cria Engine SQLAlchemy com pool_pre_ping para manter conexões válidas."""
    return create_engine(get_db_url(), pool_pre_ping=True)


# --- Auth helpers ---
def hash_password(plain: str) -> str:
    """Gera hash de senha com pbkdf2."""
    return pbkdf2_sha256.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica senha contra hash pbkdf2/bcrypt."""
    try:
        if not hashed:
            return False
        if hashed.startswith("$pbkdf2-sha256$"):
            return pbkdf2_sha256.verify(plain, hashed)
        return bcrypt.verify(plain, hashed)
    except Exception:
        return False


def make_dummy_token(user_id: int) -> str:
    """Token simples (compatível com seu frontend atual)."""
    return f"dummy-{user_id}-{int(datetime.utcnow().timestamp())}"


def parse_dummy_token(token: str) -> Optional[int]:
    """
    Espera formato: dummy-<id>-<ts>
    Retorna user_id ou None.
    """
    try:
        parts = (token or "").strip().split("-")
        if len(parts) < 3:
            return None
        if parts[0] != "dummy":
            return None
        return int(parts[1])
    except Exception:
        return None


# --- Models ---
class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RegisterIn(BaseModel):
    """Mantido por compatibilidade do código, mas endpoint será bloqueado."""
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
    id: int
    tag: str
    unit: Optional[str] = None


class MeasurementPoint(BaseModel):
    ts: datetime
    tag: str
    value: float
    unit: Optional[str] = None


class LimitsOut(BaseModel):
    limits: Dict[str, float]


class DashboardKPI(BaseModel):
    id: str
    label: str
    value: Optional[float]
    unit: Optional[str]
    limit: Optional[float] = None
    category: str = "default"
    updated_at: datetime


class DashboardOut(BaseModel):
    meta: Dict[str, str]
    data: Dict[str, Dict[str, List[DashboardKPI]]]


class LimitsIn(BaseModel):
    limits: Dict[str, float]


class AlarmsIn(BaseModel):
    alarms_enabled: bool


# --- Admin models ---
class AdminCreateUserIn(BaseModel):
    name: str
    email: EmailStr
    role: str = "user"
    password: Optional[str] = None  # se não vier, geramos uma temporária

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        v = (v or "").strip()
        if len(v) < 2:
            raise ValueError("Nome muito curto")
        return v

    @field_validator("role")
    @classmethod
    def _validate_role(cls, v: str) -> str:
        v = (v or "user").strip().lower()
        if v not in ("user", "admin"):
            raise ValueError("role inválida (use 'user' ou 'admin')")
        return v


class AdminCreateUserOut(BaseModel):
    ok: bool
    user_id: int
    email: EmailStr
    name: str
    role: str
    temporary_password: Optional[str] = None


# --- App ---
app = FastAPI(title="Aqualink API", version="0.1.0")

# CORS (produção: defina CORS_ORIGINS="http://SEU_DOMINIO,http://IP:3000")
cors_origins_raw = os.getenv("CORS_ORIGINS", "").strip()
if cors_origins_raw:
    allow_origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]
else:
    # fallback para ambiente de testes
    allow_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LOCAL_TZ = os.getenv("LOCAL_TZ", os.getenv("TZ", "America/Fortaleza"))
FEED_INTERVAL = int(os.getenv("FEED_INTERVAL", "5"))

# Agora, por padrão, apontamos explicitamente para public.config_sistema
# (isso evita depender do search_path)
CONFIG_SISTEMA_TABLE = (os.getenv("CONFIG_SISTEMA_TABLE", "public.config_sistema").strip()
                        or "public.config_sistema")


def categorize(tag: str) -> str:
    tl = (tag or "").lower()
    if tl.startswith("qualidade/"):
        return "qualidade_da_agua"
    if tl.startswith("decantacao/") or tl.startswith("bombeamento/") or tl.startswith("pressao/") or tl.startswith("nivel/"):
        return "operacional"
    return "default"


def _sanitize_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce").dt.tz_convert(LOCAL_TZ).dt.tz_localize(None)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["ts", "value"]).sort_values("ts")
    return df


# -------------------------
# Auth / Security (server)
# -------------------------
def _extract_token(
    authorization: Optional[str],
    x_auth_token: Optional[str],
) -> str:
    """
    Aceita:
      - Authorization: Bearer <token>
      - X-Auth-Token: <token>   (fallback para facilitar integração)
    """
    if x_auth_token:
        return x_auth_token.strip()

    if not authorization:
        return ""

    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()

    return ""


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    x_auth_token: Optional[str] = Header(default=None, alias="X-Auth-Token"),
) -> Dict[str, Any]:
    """
    Lê token e resolve usuário no banco.
    Token atual é dummy-<id>-<ts>.
    """
    token = _extract_token(authorization, x_auth_token)
    if not token:
        raise HTTPException(status_code=401, detail="Token ausente")

    user_id = parse_dummy_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    eng = get_engine()
    with eng.connect() as conn:
        row = conn.execute(
            text("""SELECT id, email, name, role
                    FROM eta.app_user
                    WHERE id = :id;"""),
            {"id": user_id},
        ).fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Usuário do token não encontrado")

    m = row._mapping
    return {
        "id": m["id"],
        "email": m["email"],
        "name": m.get("name") or m["email"],
        "role": (m.get("role") or "user").lower(),
    }


def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if (user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin")
    return user


# -------------------------
# Auth endpoints
# -------------------------
@app.post("/auth/login")
def auth_login(payload: LoginIn):
    eng = get_engine()
    with eng.connect() as conn:
        row = conn.execute(
            text(
                """SELECT id, email, name, password_hash, role
                   FROM eta.app_user
                   WHERE lower(email)=:e;"""
            ),
            {"e": payload.email.lower().strip()},
        ).fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    m = row._mapping
    ok = verify_password(payload.password, m.get("password_hash"))
    if not ok:
        raise HTTPException(status_code=401, detail="Senha inválida")

    token = make_dummy_token(int(m["id"]))
    return {
        "token": token,
        "user": {
            "id": m["id"],
            "email": m["email"],
            "name": m.get("name") or m["email"],
            "role": (m.get("role") or "user"),
        },
    }


@app.post("/auth/register")
def auth_register(_: RegisterIn):
    """
    Cadastro público DESATIVADO (cadastro fechado).
    Use endpoints /admin/* para criar usuários.
    """
    raise HTTPException(status_code=403, detail="Cadastro público desativado. Solicite acesso ao administrador.")


# -------------------------
# Admin endpoints
# -------------------------
@app.post("/admin/users", response_model=AdminCreateUserOut)
def admin_create_user(payload: AdminCreateUserIn, _: Dict[str, Any] = Depends(require_admin)):
    """
    Cria usuário na tabela eta.app_user.
    - Se payload.password não vier, gera senha temporária forte e retorna.
    - role default: user
    """
    email = payload.email.lower().strip()
    name = payload.name.strip()
    role = (payload.role or "user").lower().strip()

    temp_password = None
    plain_password = payload.password

    if not plain_password:
        temp_password = f"AqLk!{secrets.token_urlsafe(10)}1aA"
        plain_password = temp_password

    password_hash = hash_password(plain_password)

    eng = get_engine()
    with eng.begin() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM eta.app_user WHERE lower(email)=:e;"),
            {"e": email},
        ).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="E-mail já cadastrado")

        row = conn.execute(
            text(
                """
                INSERT INTO eta.app_user (email, name, password_hash, role, created_at, updated_at)
                VALUES (:email, :name, :ph, :role, now(), now())
                RETURNING id;
                """
            ),
            {"email": email, "name": name, "ph": password_hash, "role": role},
        ).fetchone()

    user_id = int(row._mapping["id"])
    return {
        "ok": True,
        "user_id": user_id,
        "email": email,
        "name": name,
        "role": role,
        "temporary_password": temp_password,
    }


# -------------------------
# Sensors
# -------------------------
@app.get("/sensors", response_model=List[SensorOut])
def list_sensors():
    eng = get_engine()
    with eng.connect() as conn:
        rows = conn.execute(text("SELECT id, tag, unit FROM eta.sensor ORDER BY id;")).fetchall()
    return [{"id": r._mapping["id"], "tag": r._mapping["tag"], "unit": r._mapping.get("unit")} for r in rows]


# -------------------------
# Measurements
# -------------------------
@app.get("/measurements/latest", response_model=List[MeasurementPoint])
def latest_by_sensor():
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

    return [
        {
            "ts": r._mapping["ts"],
            "tag": r._mapping["tag"],
            "value": float(r._mapping["value"]),
            "unit": r._mapping.get("unit"),
        }
        for r in rows
    ]


@app.get("/measurements/series")
def series(tags: str, minutes: int = 60):
    tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
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

    data: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        tag = r._mapping["tag"]
        data.setdefault(tag, []).append(
            {
                "ts": r._mapping["ts"],
                "value": float(r._mapping["value"]),
                "unit": r._mapping.get("unit"),
            }
        )
    return data


# -------------------------
# Limits
# -------------------------
@app.get("/limits", response_model=LimitsOut)
def get_limits():
    eng = get_engine()
    with eng.connect() as conn:
        rows = conn.execute(text("SELECT tag, limite FROM eta.config_limites;")).fetchall()

    limits: Dict[str, float] = {}
    for r in rows:
        try:
            limits[r._mapping["tag"]] = float(r._mapping["limite"])
        except Exception:
            continue

    return {"limits": limits}


@app.put("/limits")
def put_limits(payload: LimitsIn, _: Dict[str, Any] = Depends(require_admin)):
    eng = get_engine()
    with eng.begin() as conn:
        for tag, lim in (payload.limits or {}).items():
            conn.execute(
                text(
                    """
                    INSERT INTO eta.config_limites(tag, limite)
                    VALUES (:tag, :limite)
                    ON CONFLICT(tag) DO UPDATE SET limite=EXCLUDED.limite, updated_at=now();
                    """
                ),
                {"tag": tag, "limite": float(lim)},
            )
    return {"ok": True}


# -------------------------
# Alarms status
# -------------------------
def _ensure_config_sistema_row(conn) -> None:
    """
    Garante que exista config_sistema(id=1) na tabela CONFIG_SISTEMA_TABLE.
    """
    row = conn.execute(text(f"SELECT id FROM {CONFIG_SISTEMA_TABLE} WHERE id=1;")).fetchone()
    if row:
        return

    conn.execute(
        text(f"INSERT INTO {CONFIG_SISTEMA_TABLE}(id, alarms_enabled, updated_at) VALUES (1, TRUE, now());")
    )


@app.get("/alarms/status")
def alarms_status():
    """
    GET pode ser público (somente leitura).
    """
    eng = get_engine()
    with eng.begin() as conn:
        _ensure_config_sistema_row(conn)
        row = conn.execute(text(f"SELECT alarms_enabled FROM {CONFIG_SISTEMA_TABLE} WHERE id=1;")).fetchone()

    return {"alarms_enabled": bool(row._mapping["alarms_enabled"]) if row else True}


@app.put("/alarms/status")
def set_alarms(payload: AlarmsIn, _: Dict[str, Any] = Depends(require_admin)):
    """
    PUT protegido: somente admin.
    Retorna alarms_enabled para o frontend usar como fonte de verdade.
    """
    enabled = bool(payload.alarms_enabled)

    eng = get_engine()
    with eng.begin() as conn:
        _ensure_config_sistema_row(conn)
        conn.execute(
            text(f"UPDATE {CONFIG_SISTEMA_TABLE} SET alarms_enabled=:v, updated_at=now() WHERE id=1;"),
            {"v": enabled},
        )

        # Lê de volta para garantir consistência
        row = conn.execute(text(f"SELECT alarms_enabled FROM {CONFIG_SISTEMA_TABLE} WHERE id=1;")).fetchone()

    return {"ok": True, "alarms_enabled": bool(row._mapping["alarms_enabled"]) if row else enabled}


# -------------------------
# Dashboard
# -------------------------
@app.get("/dashboard", response_model=DashboardOut)
def dashboard():
    eng = get_engine()
    with eng.connect() as conn:
        last = conn.execute(
            text(
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
        ).fetchall()

        lim_rows = conn.execute(text("SELECT tag, limite FROM eta.config_limites;")).fetchall()

    limits: Dict[str, float] = {}
    for r in lim_rows:
        try:
            limits[r._mapping["tag"]] = float(r._mapping["limite"])
        except Exception:
            continue

    eta_kpis: List[DashboardKPI] = []
    for r in last:
        tag = r._mapping["tag"]
        val = float(r._mapping["value"]) if r._mapping["value"] is not None else None
        unit = r._mapping.get("unit")
        eta_kpis.append(
            DashboardKPI(
                id=tag.replace("/", "_"),
                label=tag if not unit else f"{tag} ({unit})",
                value=val,
                unit=unit,
                limit=limits.get(tag),
                category=categorize(tag),
                updated_at=r._mapping["ts"],
            )
        )

    data = {
        "eta": {"kpis": eta_kpis},
        "ultrafiltracao": {"kpis": []},
        "carvao": {"kpis": []},
    }
    return {"meta": {"timestamp": datetime.utcnow().isoformat(), "status": "online"}, "data": data}


# -------------------------
# Reports
# -------------------------
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
        df = (
            pd.DataFrame(rows, columns=["ts", "tag", "value", "unit", "quality", "meta"])
            if rows
            else pd.DataFrame(columns=["ts", "tag", "value", "unit", "quality", "meta"])
        )

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

            seconds = max(0, int((now - start).total_seconds()))
            esperado = max(1, seconds // FEED_INTERVAL)
            resumo["completude_%"] = (resumo["Qtd de Leitura"] / esperado * 100).clip(upper=100).round(1)

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

            resumo.to_excel(xw, sheet_name="Resumo", index=False)
            diario.to_excel(xw, sheet_name="Diario", index=False)
            horario.to_excel(xw, sheet_name="Horario", index=False)
            bruto.to_excel(xw, sheet_name="Bruto", index=False)

            for name, data_tbl in [("Resumo", resumo), ("Diario", diario), ("Horario", horario), ("Bruto", bruto)]:
                ws = xw.sheets[name]
                ws.freeze_panes(1, 1)
                _autosize(ws, data_tbl)

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=relatorio_{period}.xlsx"},
    )


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

        df = (
            pd.DataFrame(rows, columns=["ts", "tag", "value", "unit", "quality", "meta"])
            if rows
            else pd.DataFrame(columns=["ts", "tag", "value", "unit", "quality", "meta"])
        )

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

            seconds = max(0, int((end_dt - start_dt).total_seconds()))
            esperado = max(1, seconds // FEED_INTERVAL)
            resumo["completude_%"] = (resumo["Qtd de Leitura"] / esperado * 100).clip(upper=100).round(1)

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
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )


@app.get("/")
def root():
    return {"ok": True, "service": "Aqualink API"}

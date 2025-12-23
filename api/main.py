import os
import secrets
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict

from fastapi import FastAPI, HTTPException, Depends, Header
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
import requests 

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
    if url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and "postgresql+psycopg://" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url

# Monta URL do banco a partir de envs
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

def get_engine() -> Engine:
    return create_engine(get_db_url(), pool_pre_ping=True)

# --- Auth helpers ---
def hash_password(plain: str) -> str:
    return pbkdf2_sha256.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        if hashed.startswith("$pbkdf2-sha256$"):
            return pbkdf2_sha256.verify(plain, hashed)
        return bcrypt.verify(plain, hashed)
    except Exception:
        return False

# Função simples para extrair usuário do token (Baseado no seu padrão dummy-id-ts)
def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente")
    
    # O front costuma mandar "Bearer <token>" ou apenas o token
    token = authorization.replace("Bearer ", "").strip()
    
    try:
        # Formato esperado: dummy-{id}-{timestamp}
        parts = token.split("-")
        if len(parts) < 3 or parts[0] != "dummy":
            raise HTTPException(status_code=401, detail="Token inválido")
        
        user_id = int(parts[1])
        return user_id
    except:
        raise HTTPException(status_code=401, detail="Token malformado")

# Dependência para garantir que é admin
def get_current_admin(user_id: int = Depends(get_current_user)):
    eng = get_engine()
    with eng.connect() as conn:
        row = conn.execute(text("SELECT role FROM eta.app_user WHERE id=:id"), {"id": user_id}).fetchone()
        if not row or row._mapping["role"] != 'admin':
             raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return user_id

# --- Brevo Email Helper ---
def send_brevo_invite(to_email: str, invite_link: str):
    url = "https://api.brevo.com/v3/smtp/email"
    api_key = os.getenv("BREVO_API_KEY")
    sender_email = os.getenv("ALERT_SENDER_EMAIL", "admin@aqualink.com")
    sender_name = os.getenv("ALERT_SENDER_NAME", "Aqualink Admin")

    if not api_key:
        print("AVISO: BREVO_API_KEY não configurada. E-mail não enviado.")
        return

    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": to_email}],
        "subject": "Convite para acessar o Aqualink-EQ",
        "htmlContent": f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f4f4f5;">
            <div style="max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);">
                <!-- Header com Logo (Removida imagem, apenas texto ou barra) -->
                <div style="background: linear-gradient(135deg, #00B2E2 0%, #0075A9 100%); padding: 40px 0; text-align: center;">
                   <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Aqualink EQ</h1>
                </div>

                <!-- Conteúdo Principal -->
                <div style="padding: 40px 32px; text-align: center;">
                    <h2 style="color: #1e293b; font-size: 24px; font-weight: 600; margin: 0 0 16px 0;">Bem-vindo(a) à equipe!</h2>
                    
                    <p style="color: #64748b; font-size: 16px; line-height: 1.6; margin: 0 0 32px 0;">
                        Você foi convidado para criar uma <strong>conta operacional</strong> no sistema Aqualink-EQ.
                        <br>Para começar, clique no botão abaixo e defina sua senha de acesso.
                    </p>

                    <!-- Botão de Ação -->
                    <a href="{invite_link}" style="display: inline-block; background-color: #00B2E2; color: #ffffff; font-weight: 600; text-decoration: none; padding: 14px 32px; border-radius: 8px; transition: background-color 0.2s;">
                        Aceitar Convite
                    </a>

                    <div style="margin-top: 32px; padding-top: 32px; border-top: 1px solid #e2e8f0;">
                        <p style="color: #94a3b8; font-size: 13px; margin: 0 0 8px 0;">
                            Se o botão não funcionar, copie e cole o link abaixo no seu navegador:
                        </p>
                        <a href="{invite_link}" style="color: #0075A9; font-size: 13px; text-decoration: none; word-break: break-all;">
                            {invite_link}
                        </a>
                    </div>
                </div>

                <!-- Footer -->
                <div style="background-color: #f8fafc; padding: 24px; text-align: center; border-top: 1px solid #e2e8f0;">
                    <p style="color: #94a3b8; font-size: 12px; margin: 0;">
                        Este link de convite expira em 24 horas.
                        <br>
                        © {datetime.now().year} Aqualink EQ. Todos os direitos reservados.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    }
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": api_key
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Erro ao enviar email Brevo: {e}")
        # Não damos raise no erro para não travar o admin, mas logamos
        raise HTTPException(status_code=500, detail="Erro ao enviar e-mail de convite.")

# --- Models ---
class LoginIn(BaseModel):
    email: EmailStr
    password: str

class InviteIn(BaseModel):
    """Admin informa o email para convidar."""
    email: EmailStr

class RegisterInviteIn(BaseModel):
    """Usuário completa o cadastro enviando o token + dados."""
    token: str
    name: str
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

class UserOut(BaseModel):
    """Modelo seguro para listar usuários (sem senha)."""
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool

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


app = FastAPI(title="Aqualink API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def categorize(tag: str) -> str:
    tl = tag.lower()
    if tl.startswith("qualidade/"):
        return "qualidade_da_agua"
    if tl.startswith("decantacao/") or tl.startswith("bombeamento/") or tl.startswith("pressao/") or tl.startswith("nivel/"):
        return "operacional"
    return "default"

LOCAL_TZ = os.getenv("LOCAL_TZ", os.getenv("TZ", "America/Fortaleza"))
FEED_INTERVAL = int(os.getenv("FEED_INTERVAL", "5"))

def _sanitize_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df["ts"] = (
        pd.to_datetime(df["ts"], utc=True, errors="coerce").dt.tz_convert(LOCAL_TZ).dt.tz_localize(None)
    )
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["ts", "value"]) .sort_values("ts")
    return df


# --- Auth Endpoints (NEW FLOW) ---

@app.post("/auth/login")
def auth_login(payload: LoginIn):
    eng = get_engine()
    with eng.connect() as conn:
        row = conn.execute(
            text("""SELECT id, email, name, password_hash, role
                    FROM eta.app_user WHERE lower(email)=:e;"""),
            {"e": payload.email.lower().strip()},
        ).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        ok = verify_password(payload.password, row._mapping["password_hash"])
        if not ok:
            raise HTTPException(status_code=401, detail="Senha inválida")
        
        # Token dummy (em produção idealmente seria JWT)
        token = f"dummy-{row._mapping['id']}-{int(datetime.utcnow().timestamp())}"
        
        return {
            "token": token, 
            "user": {
                "id": row._mapping["id"], 
                "email": row._mapping["email"], 
                "name": row._mapping.get("name") or row._mapping["email"], 
                "role": row._mapping.get("role", "user")
            }
        }

@app.post("/auth/invite")
def create_invite(payload: InviteIn, current_user_id: int = Depends(get_current_admin)):
    """Apenas ADMIN pode convidar novos usuários."""
    eng = get_engine()
    
    # 1. Verificar se usuário já existe
    with eng.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM eta.app_user WHERE lower(email)=:e"), 
            {"e": payload.email.lower().strip()}
        ).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="Este e-mail já possui conta ativa.")

    # 2. Gerar Token e Data de Expiração (24h)
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    # 3. Salvar no Banco
    with eng.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO eta.user_invites (token, email, created_by, expires_at)
                VALUES (:tok, :email, :uid, :exp)
            """),
            {"tok": token, "email": payload.email.lower().strip(), "uid": current_user_id, "exp": expires_at}
        )
    
    # 4. Enviar E-mail
    frontend_url = os.getenv("FRONTEND_URL")
    if not frontend_url:
        frontend_url = "http://localhost:3000"
        
    link = f"{frontend_url}/register?token={token}"
    
    send_brevo_invite(payload.email, link)
    
    return {"ok": True, "message": f"Convite enviado para {payload.email}"}

@app.get("/auth/validate-invite/{token}")
def validate_invite(token: str):
    """Verifica se o token é válido para mostrar o formulário no front."""
    eng = get_engine()
    with eng.connect() as conn:
        row = conn.execute(
            text("""
                SELECT email, expires_at, used 
                FROM eta.user_invites 
                WHERE token = :tok
            """), 
            {"tok": token}
        ).fetchone()
        
    if not row:
        raise HTTPException(status_code=404, detail="Convite inválido.")
    
    if row._mapping["used"]:
        raise HTTPException(status_code=400, detail="Este convite já foi utilizado.")
        
    if datetime.utcnow() > row._mapping["expires_at"]:
        raise HTTPException(status_code=400, detail="Este convite expirou.")
        
    return {"valid": True, "email": row._mapping["email"]}

@app.post("/auth/register-invite")
def register_with_invite(payload: RegisterInviteIn):
    """Cria o usuário validando o token."""
    eng = get_engine()
    
    # 1. Validar Token novamente (segurança dupla)
    with eng.connect() as conn:
        invite = conn.execute(
            text("SELECT email, used, expires_at FROM eta.user_invites WHERE token=:tok"),
            {"tok": payload.token}
        ).fetchone()
        
    if not invite:
        raise HTTPException(status_code=404, detail="Convite não encontrado.")
        
    if invite._mapping["used"] or datetime.utcnow() > invite._mapping["expires_at"]:
        raise HTTPException(status_code=400, detail="Convite inválido ou expirado.")

    email_convite = invite._mapping["email"]
    
    # 2. Verificar novamente se usuário já existe (race condition)
    with eng.connect() as conn:
         exists = conn.execute(
            text("SELECT 1 FROM eta.app_user WHERE lower(email)=:e"), 
            {"e": email_convite}
        ).fetchone()
         if exists:
             raise HTTPException(status_code=409, detail="Usuário já cadastrado.")

    # 3. Criar Usuário e Invalidar Token
    pwd_hash = hash_password(payload.password)
    
    with eng.begin() as conn:
        # Cria user
        conn.execute(
            text("""INSERT INTO eta.app_user(email, name, password_hash, role, is_active)
                    VALUES (:e, :n, :p, 'user', TRUE);"""),
            {"e": email_convite, "n": payload.name.strip(), "p": pwd_hash},
        )
        # Queima o token
        conn.execute(
            text("UPDATE eta.user_invites SET used=TRUE WHERE token=:tok"),
            {"tok": payload.token}
        )
        
    return {"ok": True, "message": "Conta criada com sucesso! Faça login."}

@app.get("/auth/users", response_model=List[UserOut])
def list_users(current_user_id: int = Depends(get_current_admin)):
    """Lista todos os usuários cadastrados (Apenas Admin)."""
    eng = get_engine()
    with eng.connect() as conn:
        # Selecionamos apenas dados seguros
        rows = conn.execute(text("""
            SELECT id, name, email, role, is_active 
            FROM eta.app_user 
            ORDER BY id ASC
        """)).fetchall()
        
        return [
            {
                "id": r._mapping["id"],
                "name": r._mapping.get("name") or "Sem Nome",
                "email": r._mapping["email"],
                "role": r._mapping["role"],
                "is_active": r._mapping["is_active"]
            }
            for r in rows
        ]

@app.delete("/auth/users/{user_id}")
def delete_user(user_id: int, current_user_id: int = Depends(get_current_admin)):
    """Remove (ou desativa) um usuário pelo ID."""
    
    # Previne que o admin se delete a si mesmo
    if user_id == current_user_id:
        raise HTTPException(status_code=400, detail="Você não pode excluir sua própria conta.")

    eng = get_engine()
    with eng.begin() as conn: # Usar begin() para transação (commit automático)
        # Opção A: Hard Delete (apaga do banco)
        result = conn.execute(text("DELETE FROM eta.app_user WHERE id=:id"), {"id": user_id})
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
            
    return {"ok": True, "message": "Usuário removido com sucesso."}


# --- Sensors ---
@app.get("/sensors", response_model=List[SensorOut])
def list_sensors():
    eng = get_engine()
    with eng.connect() as conn:
        rows = conn.execute(text("SELECT id, tag, unit FROM eta.sensor ORDER BY id; ")).fetchall()
        return [{"id": r._mapping["id"], "tag": r._mapping["tag"], "unit": r._mapping["unit"]} for r in rows]

# --- Measurements ---
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
        return [{"ts": r._mapping["ts"], "tag": r._mapping["tag"], "value": float(r._mapping["value"]), "unit": r._mapping.get("unit") } for r in rows]

@app.get("/measurements/series")
def series(tags: str, minutes: int = 60):
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

@app.put("/limits")
def put_limits(payload: LimitsIn):
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
    return {"ok": True, "service": "Aqualink API", "version": "0.2.0"}
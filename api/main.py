from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from routers import auth, dashboard, reports, measurements, limits, alarms, sensors
from core.config import settings
from database.connection import get_engine

app = FastAPI(title="Aqualink API", version="0.2.0")

# CORS restrito às origens configuradas (antes era "*", aberto a qualquer site).
# CORS_ORIGINS pode listar várias origens separadas por vírgula; se vazio, cai
# no FRONTEND_URL. Defina a origem real do dashboard no .env em produção.
_cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()] or [settings.FRONTEND_URL]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])
app.include_router(measurements.router, tags=["Sensors & Data"])
app.include_router(limits.router, tags=["Limits"])
app.include_router(alarms.router, tags=["Alarms"])
app.include_router(sensors.router, tags=["Sensors"])

@app.get("/")
def root():
    """
    Rota raiz para verificação de saúde da API.

    Retorna:
        dict: Um dicionário contendo status, nome do serviço e versão.
    """
    return {"ok": True, "service": "Aqualink API", "version": "0.2.0"}


@app.get("/health")
def health():
    """
    Healthcheck real: verifica a conectividade com o banco (SELECT 1).
    Retorna 503 se o banco estiver inacessível.
    """
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"ok": True, "db": "up"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"ok": False, "db": "down", "error": str(e)})
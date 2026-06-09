from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, dashboard, reports, measurements, limits, alarms
from core.config import settings

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

@app.get("/")
def root():
    """
    Rota raiz para verificação de saúde da API.
    
    Retorna:
        dict: Um dicionário contendo status, nome do serviço e versão.
    """
    return {"ok": True, "service": "Aqualink API", "version": "0.2.0"}
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, dashboard, reports, measurements, limits, alarms

app = FastAPI(title="Aqualink API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
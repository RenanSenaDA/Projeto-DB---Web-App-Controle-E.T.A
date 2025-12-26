"""
Arquivo principal da aplicação FastAPI Aqualink API.

Este módulo inicializa a aplicação FastAPI, configura middlewares (CORS) e registra as rotas.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, dashboard, reports        

app = FastAPI(
    title="Aqualink API", 
    version="0.2.0",
    description="API para monitoramento e gestão de qualidade da água (Aqualink EQ)."
)

# Configuração do CORS para permitir acesso de qualquer origem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra as rotas da aplicação
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])

@app.get("/")
def root():
    """
    Rota raiz para verificação de saúde da API.
    
    Retorna:
        dict: Um dicionário contendo status, nome do serviço e versão.
    """
    return {"ok": True, "service": "Aqualink API", "version": "0.2.0"}
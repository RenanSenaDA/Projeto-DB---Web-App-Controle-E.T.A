"""
Módulo de configuração da aplicação.

Carrega variáveis de ambiente e define a classe Settings com as configurações globais.
"""

import os
from dotenv import load_dotenv, find_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv(find_dotenv())
for extra in [os.path.join(os.getcwd(), ".env")]:
    if os.path.exists(extra):
        load_dotenv(extra, override=False)

class Settings:
    """
    Classe contendo as configurações da aplicação.
    """
    # Configurações de Banco de Dados
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    PGHOST: str = os.getenv("PGHOST", os.getenv("DB_HOST", "localhost"))
    PGPORT: str = os.getenv("PGPORT", os.getenv("DB_PORT", "5432"))
    PGUSER: str = os.getenv("PGUSER", os.getenv("POSTGRES_USER", "postgres"))
    PGPASSWORD: str = os.getenv("PGPASSWORD", os.getenv("POSTGRES_PASSWORD", "postgres"))
    PGDATABASE: str = os.getenv("PGDATABASE", os.getenv("POSTGRES_DB", "eta"))
    
    # Configurações da Aplicação
    LOCAL_TZ: str = os.getenv("LOCAL_TZ", os.getenv("TZ", "America/Fortaleza"))
    FEED_INTERVAL: int = int(os.getenv("FEED_INTERVAL", "5"))
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Configurações de Email (Brevo)
    BREVO_API_KEY: str = os.getenv("BREVO_API_KEY", "")
    ALERT_SENDER_EMAIL: str = os.getenv("ALERT_SENDER_EMAIL", "admin@aqualink.com")
    ALERT_SENDER_NAME: str = os.getenv("ALERT_SENDER_NAME", "Aqualink Admin")

settings = Settings()
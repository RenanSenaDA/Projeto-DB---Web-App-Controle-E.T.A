"""
Módulo de conexão com o banco de dados.

Gerencia a criação da engine SQLAlchemy e formatação da URL de conexão.
"""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from core.config import settings

def to_sqlalchemy_url(url: str) -> str:
    """
    Converte URLs de conexão para o formato suportado pelo SQLAlchemy/Psycopg.
    
    Args:
        url (str): URL de conexão original.
        
    Returns:
        str: URL de conexão formatada.
    """
    if not url: return url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and "postgresql+psycopg://" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url

def get_db_url() -> str:
    """
    Obtém a URL de conexão com o banco de dados a partir das configurações.
    
    Returns:
        str: URL de conexão completa.
    """
    url = settings.DATABASE_URL.strip()
    if url:
        return to_sqlalchemy_url(url)
    return f"postgresql+psycopg://{settings.PGUSER}:{settings.PGPASSWORD}@{settings.PGHOST}:{settings.PGPORT}/{settings.PGDATABASE}"

# Engine criada uma única vez e reusada em todo o processo (singleton de módulo).
# Antes era recriada a cada chamada de get_engine() (~18 call sites, às vezes 2x
# por request), descartando o connection pool e podendo esgotar as conexões da RDS.
_engine: Engine | None = None


def get_engine() -> Engine:
    """
    Retorna a engine SQLAlchemy compartilhada, criando-a na primeira chamada.

    A engine (e seu connection pool) é reusada entre requests. SQLAlchemy
    Engine é thread-safe para uso concorrente.

    Returns:
        Engine: Engine configurada com pool_pre_ping=True.
    """
    global _engine
    if _engine is None:
        _engine = create_engine(get_db_url(), pool_pre_ping=True)
    return _engine
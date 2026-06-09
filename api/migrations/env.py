"""Ambiente de execução do Alembic.

A URL do banco vem da configuração da aplicação (database.connection.get_db_url),
que lê DATABASE_URL ou as variáveis PG* do .env. Assim há uma única fonte da
verdade para a conexão, sem credenciais no alembic.ini.

As migrações deste projeto são SQL escrito à mão (o código usa SQL parametrizado,
não um ORM), portanto não há metadata para autogenerate — as revisões são criadas
manualmente com `alembic revision -m "..."`.
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Garante que os módulos da app (database.connection, core.config) sejam
# importáveis tanto rodando a partir de api/ (local) quanto de /app (container).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_url  # noqa: E402

config = context.config

# Injeta a URL de conexão a partir da configuração da aplicação.
config.set_main_option("sqlalchemy.url", get_db_url())

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Sem ORM -> sem metadata. Migrações são SQL explícito.
target_metadata = None


def run_migrations_offline() -> None:
    """Modo offline: gera o SQL (`alembic upgrade head --sql`) sem conectar ao banco."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Modo online: conecta ao banco e aplica as migrações."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

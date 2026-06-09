"""baseline: schema eta REAL de produção (modelo plano sensor+measurement)

Revision ID: 0001_baseline_schema
Revises:
Create Date: 2026-06-09

Baseline da adoção do Alembic. Representa o estado REAL do schema `eta` em
produção (introspeccionado do banco), que é um **modelo plano** — bem diferente
do antigo `01_schema.sql` (normalizado, que nunca existiu de fato no banco).

Tabelas reais: sensor, measurement, app_user, user_invites, config_limites,
config_sistema. IDs de sensor/measurement.sensor_id são TEXT; measurement.quality
é TEXT; measurement carrega tag/unit desnormalizados.

ADOÇÃO EM PRODUÇÃO: use `alembic stamp head` (marca a versão, NÃO roda este DDL),
pois o banco já existe. O `upgrade()` abaixo (idempotente) serve para criar o
schema em bancos NOVOS (dev/test). Mudanças futuras: novas revisões aplicadas
com `alembic upgrade head`.

Cruft conhecido em produção, NÃO reproduzido aqui (candidato a limpeza via
revisão futura): tabela órfã `user_invite` (singular, sem uso no código),
constraint UNIQUE duplicada em app_user.email, e FK duplicada/conflitante em
measurement.sensor_id.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_baseline_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Statements idempotentes, executados em ordem. O SET search_path faz os nomes
# não qualificados resolverem no schema `eta`.
STATEMENTS = [
    "CREATE SCHEMA IF NOT EXISTS eta;",
    "SET search_path TO eta, public;",

    # ----- Sensores (id TEXTUAL com sequência própria, como em produção) -----
    "CREATE SEQUENCE IF NOT EXISTS sensor_id_seq;",
    """
    CREATE TABLE IF NOT EXISTS sensor (
      id    TEXT NOT NULL DEFAULT nextval('eta.sensor_id_seq'::regclass) PRIMARY KEY,
      tag   TEXT NOT NULL UNIQUE,
      unit  TEXT,
      meta  JSONB
    );
    """,

    # ----- Medições (modelo plano: sensor_id textual + tag/unit desnormalizados) -----
    """
    CREATE TABLE IF NOT EXISTS measurement (
      id        BIGSERIAL PRIMARY KEY,
      sensor_id TEXT NOT NULL REFERENCES sensor(id) ON DELETE CASCADE,
      ts        TIMESTAMPTZ NOT NULL,
      value     DOUBLE PRECISION NOT NULL,
      quality   TEXT,
      meta      JSONB,
      tag       TEXT,
      unit      TEXT,
      UNIQUE (sensor_id, ts)
    );
    """,
    "CREATE INDEX IF NOT EXISTS ix_measurement_ts ON measurement (ts);",
    "CREATE INDEX IF NOT EXISTS idx_measurement_sensor ON measurement (sensor_id);",
    "CREATE INDEX IF NOT EXISTS ix_measurement_sensor_ts ON measurement (sensor_id, ts DESC);",

    # ----- Usuários -----
    """
    CREATE TABLE IF NOT EXISTS app_user (
      id            SERIAL PRIMARY KEY,
      email         TEXT NOT NULL UNIQUE,
      name          TEXT,
      password_hash TEXT NOT NULL,
      role          TEXT DEFAULT 'user',
      is_active     BOOLEAN DEFAULT TRUE,
      created_at    TIMESTAMPTZ DEFAULT now()
    );
    """,
    "CREATE INDEX IF NOT EXISTS ix_app_user_email ON app_user (lower(email));",

    # ----- Convites (tabela `user_invites` — a usada pela API) -----
    # Observação: em produção `expires_at`/`created_at` são TIMESTAMP sem timezone.
    """
    CREATE TABLE IF NOT EXISTS user_invites (
      token       VARCHAR NOT NULL PRIMARY KEY,
      email       VARCHAR NOT NULL,
      created_by  INTEGER REFERENCES app_user(id),
      expires_at  TIMESTAMP NOT NULL,
      used        BOOLEAN DEFAULT FALSE,
      created_at  TIMESTAMP DEFAULT now()
    );
    """,

    # ----- Limites por tag -----
    """
    CREATE TABLE IF NOT EXISTS config_limites (
      tag        TEXT PRIMARY KEY,
      limite     DOUBLE PRECISION NOT NULL,
      updated_at TIMESTAMPTZ DEFAULT now(),
      label      TEXT
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_config_limites_label ON config_limites (label);",

    # ----- Estado global dos alarmes -----
    """
    CREATE TABLE IF NOT EXISTS config_sistema (
      id             INTEGER PRIMARY KEY,
      alarms_enabled BOOLEAN NOT NULL DEFAULT TRUE,
      updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,
    # Registro singleton (id=1). A API trata a ausência, mas semeamos para
    # comportamento determinístico (alarmes ligados) em bancos novos.
    "INSERT INTO config_sistema(id, alarms_enabled) VALUES (1, TRUE) ON CONFLICT (id) DO NOTHING;",
]


def upgrade() -> None:
    for stmt in STATEMENTS:
        # rstrip(";") evita ";;" no SQL gerado em modo offline (alembic já
        # adiciona o terminador). Não afeta a execução online.
        op.execute(stmt.strip().rstrip(";"))


def downgrade() -> None:
    # Baseline: não há downgrade. Reverter significaria DROP de todo o schema
    # `eta` (e dos dados de produção), o que nunca deve acontecer automaticamente.
    raise RuntimeError("A migração de baseline não pode ser revertida (downgrade).")

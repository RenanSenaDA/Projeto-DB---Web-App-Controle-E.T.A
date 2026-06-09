"""baseline: schema eta completo (núcleo + tabelas de app/limites/alarmes)

Revision ID: 0001_baseline_schema
Revises:
Create Date: 2026-06-09

Esta é a migração de baseline. Ela representa o estado COMPLETO do schema `eta`
em produção no momento da adoção do Alembic, incluindo as tabelas que antes só
existiam na EC2 (schema drift): app_user, user_invites, config_limites e
config_sistema.

Todo o DDL é IDEMPOTENTE (CREATE ... IF NOT EXISTS / CREATE OR REPLACE), de modo
que aplicar esta migração:
  - num banco NOVO  -> cria todo o schema do zero;
  - no banco ATUAL  -> é um no-op no que já existe e apenas registra a versão.

Por isso `alembic upgrade head` é seguro tanto localmente quanto no RDS de
produção (não é necessário `alembic stamp`).
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_baseline_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Cada item é um único statement DDL idempotente. São executados em ordem,
# dentro da transação da migração. O SET search_path faz os nomes não
# qualificados (site, measurement, ...) resolverem no schema `eta`.
STATEMENTS = [
    "CREATE SCHEMA IF NOT EXISTS eta;",
    "SET search_path TO eta, public;",

    # ----- 1) Local/Unidades/Dispositivos -----
    """
    CREATE TABLE IF NOT EXISTS site (
      id        SERIAL PRIMARY KEY,
      name      TEXT NOT NULL,
      city      TEXT,
      state     TEXT,
      timezone  TEXT DEFAULT 'UTC',
      meta      JSONB
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS unit (
      id        SERIAL PRIMARY KEY,
      site_id   INT NOT NULL REFERENCES site(id) ON DELETE CASCADE,
      name      TEXT NOT NULL,
      process   TEXT,
      meta      JSONB
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS device (
      id        SERIAL PRIMARY KEY,
      unit_id   INT NOT NULL REFERENCES unit(id) ON DELETE CASCADE,
      vendor    TEXT,
      model     TEXT,
      serial    TEXT UNIQUE,
      protocol  TEXT,
      meta      JSONB
    );
    """,

    # ----- 2) Sensores/Tags -----
    """
    CREATE TABLE IF NOT EXISTS sensor (
      id          SERIAL PRIMARY KEY,
      device_id   INT NOT NULL REFERENCES device(id) ON DELETE CASCADE,
      tag         TEXT NOT NULL UNIQUE,
      name        TEXT,
      unit        TEXT,
      description TEXT,
      min_valid   DOUBLE PRECISION,
      max_valid   DOUBLE PRECISION,
      decimals    INT DEFAULT 3,
      meta        JSONB
    );
    """,

    # ----- 3) Gateways -----
    """
    CREATE TABLE IF NOT EXISTS gateway (
      id        SERIAL PRIMARY KEY,
      name      TEXT NOT NULL,
      version   TEXT,
      last_ip   INET,
      meta      JSONB
    );
    """,

    # ----- 4) Ingestão bruta (staging) -----
    """
    CREATE TABLE IF NOT EXISTS raw_ingest (
      id           BIGSERIAL PRIMARY KEY,
      gateway_id   INT REFERENCES gateway(id) ON DELETE SET NULL,
      received_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      src_topic    TEXT,
      payload      JSONB NOT NULL,
      status       TEXT DEFAULT 'received',
      err_msg      TEXT
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_raw_ingest_received_at ON raw_ingest (received_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_raw_ingest_payload ON raw_ingest USING GIN (payload);",

    # ----- 5) Medições curadas -----
    """
    CREATE TABLE IF NOT EXISTS measurement (
      id          BIGSERIAL PRIMARY KEY,
      sensor_id   INT NOT NULL REFERENCES sensor(id) ON DELETE CASCADE,
      ts          TIMESTAMPTZ NOT NULL,
      value       DOUBLE PRECISION NOT NULL,
      quality     BOOLEAN DEFAULT TRUE,
      meta        JSONB,
      UNIQUE(sensor_id, ts)
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_measurement_sensor_ts ON measurement (sensor_id, ts DESC);",
    "CREATE INDEX IF NOT EXISTS idx_measurement_ts ON measurement (ts DESC);",

    # ----- 6) Eventos/Alarmes -----
    """
    CREATE TABLE IF NOT EXISTS event (
      id          BIGSERIAL PRIMARY KEY,
      sensor_id   INT NOT NULL REFERENCES sensor(id) ON DELETE CASCADE,
      ts          TIMESTAMPTZ NOT NULL,
      severity    TEXT CHECK (severity IN ('info','warn','crit')) DEFAULT 'info',
      message     TEXT NOT NULL,
      meta        JSONB
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_event_sensor_ts ON event (sensor_id, ts DESC);",

    # ----- 7) Calibração -----
    """
    CREATE TABLE IF NOT EXISTS calibration (
      id        SERIAL PRIMARY KEY,
      sensor_id INT NOT NULL REFERENCES sensor(id) ON DELETE CASCADE,
      ts        TIMESTAMPTZ NOT NULL,
      method    TEXT,
      meta      JSONB
    );
    """,

    # ----- 8) Usuários e convites (antes só existiam na EC2 / drift) -----
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
    """
    CREATE TABLE IF NOT EXISTS user_invites (
      token       TEXT PRIMARY KEY,
      email       TEXT NOT NULL,
      created_by  INT REFERENCES app_user(id) ON DELETE SET NULL,
      expires_at  TIMESTAMPTZ NOT NULL,
      used        BOOLEAN NOT NULL DEFAULT FALSE,
      created_at  TIMESTAMPTZ DEFAULT now()
    );
    """,

    # ----- 9) Limites e estado dos alarmes (antes só existiam na EC2 / drift) -----
    """
    CREATE TABLE IF NOT EXISTS config_limites (
      tag        TEXT PRIMARY KEY,
      limite     DOUBLE PRECISION NOT NULL,
      updated_at TIMESTAMPTZ DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS config_sistema (
      id             INT PRIMARY KEY,
      alarms_enabled BOOLEAN DEFAULT TRUE,
      updated_at     TIMESTAMPTZ DEFAULT now()
    );
    """,
    # Registro singleton de estado dos alarmes (id=1). A API trata a ausência,
    # mas semeamos para manter o comportamento histórico (alarmes ligados).
    "INSERT INTO config_sistema(id, alarms_enabled) VALUES (1, TRUE) ON CONFLICT (id) DO NOTHING;",

    # ----- TimescaleDB opcional (cria hypertable se a extensão existir) -----
    """
    DO $$
    BEGIN
      PERFORM 1 FROM pg_extension WHERE extname = 'timescaledb';
      IF NOT FOUND THEN
        BEGIN
          CREATE EXTENSION IF NOT EXISTS timescaledb;
        EXCEPTION WHEN OTHERS THEN
          RAISE NOTICE 'TimescaleDB não disponível, seguindo sem extensão.';
        END;
      END IF;

      IF EXISTS (SELECT 1 FROM pg_extension WHERE extname='timescaledb') THEN
        PERFORM create_hypertable('measurement','ts', if_not_exists => TRUE);
      END IF;
    END$$;
    """,

    # ----- Views úteis -----
    """
    CREATE OR REPLACE VIEW v_latest_per_sensor AS
    SELECT DISTINCT ON (m.sensor_id)
      m.sensor_id, s.tag, s.unit, m.value, m.ts, m.quality
    FROM measurement m
    JOIN sensor s ON s.id = m.sensor_id
    ORDER BY m.sensor_id, m.ts DESC;
    """,
    """
    CREATE OR REPLACE VIEW v_hourly_avg_24h AS
    SELECT s.tag, date_trunc('hour', m.ts) AS hour_bucket,
           AVG(m.value) AS avg_value, MIN(m.value) AS min_value, MAX(m.value) AS max_value
    FROM measurement m
    JOIN sensor s ON s.id = m.sensor_id
    WHERE m.ts >= now() - interval '24 hours'
    GROUP BY s.tag, hour_bucket
    ORDER BY hour_bucket DESC, s.tag;
    """,
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

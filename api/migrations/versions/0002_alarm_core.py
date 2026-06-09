"""alarm core: limites bidirecionais, histórico de alarmes e config de staleness

Revision ID: 0002_alarm_core
Revises: 0001_baseline_schema
Create Date: 2026-06-09

Fundação da Fase 1 (alarmes mais robustos):
- config_limites ganha `limite_min`/`limite_max` (alarme bidirecional/por faixa).
  O `limite` legado (limite superior) é copiado para `limite_max` nas linhas
  existentes, mantendo compatibilidade.
- config_sistema ganha `stale_after_min` (minutos sem leitura para considerar um
  sensor "mudo"/offline).
- nova tabela `alarm_event`: histórico de alarmes com severidade, status
  (open/acked/resolved), reconhecimento e timestamps. Um índice único parcial
  garante no máximo 1 alarme ABERTO por (tag, kind) — serve de estado/cooldown.

Aditiva e idempotente; segura de aplicar em produção com `alembic upgrade head`.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002_alarm_core"
down_revision: Union[str, None] = "0001_baseline_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UPGRADE = [
    "SET search_path TO eta, public;",

    # --- Limites bidirecionais / por faixa ---
    "ALTER TABLE eta.config_limites ADD COLUMN IF NOT EXISTS limite_min DOUBLE PRECISION;",
    "ALTER TABLE eta.config_limites ADD COLUMN IF NOT EXISTS limite_max DOUBLE PRECISION;",
    # O `limite` legado era o limite SUPERIOR -> migra para limite_max.
    "UPDATE eta.config_limites SET limite_max = limite WHERE limite_max IS NULL AND limite IS NOT NULL;",
    # `limite` deixa de ser obrigatório: faixas só-com-mínimo deixam limite NULL.
    "ALTER TABLE eta.config_limites ALTER COLUMN limite DROP NOT NULL;",

    # --- Config de sensor mudo (global) ---
    "ALTER TABLE eta.config_sistema ADD COLUMN IF NOT EXISTS stale_after_min INTEGER NOT NULL DEFAULT 15;",

    # --- Histórico de alarmes ---
    """
    CREATE TABLE IF NOT EXISTS eta.alarm_event (
      id               BIGSERIAL PRIMARY KEY,
      sensor_id        TEXT REFERENCES eta.sensor(id) ON DELETE SET NULL,
      tag              TEXT NOT NULL,
      kind             TEXT NOT NULL,                 -- 'high' | 'low' | 'stale'
      severity         TEXT NOT NULL DEFAULT 'warn',  -- 'warn' | 'crit'
      status           TEXT NOT NULL DEFAULT 'open',  -- 'open' | 'acked' | 'resolved'
      value            DOUBLE PRECISION,
      threshold        DOUBLE PRECISION,
      message          TEXT,
      opened_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
      last_notified_at TIMESTAMPTZ,
      acked_by         INTEGER REFERENCES eta.app_user(id) ON DELETE SET NULL,
      acked_at         TIMESTAMPTZ,
      resolved_at      TIMESTAMPTZ
    );
    """,
    "CREATE INDEX IF NOT EXISTS ix_alarm_event_status ON eta.alarm_event (status);",
    "CREATE INDEX IF NOT EXISTS ix_alarm_event_tag_opened ON eta.alarm_event (tag, opened_at DESC);",
    "CREATE INDEX IF NOT EXISTS ix_alarm_event_opened ON eta.alarm_event (opened_at DESC);",
    # No máximo 1 alarme ABERTO por (tag, kind): estado/cooldown determinístico.
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_alarm_event_open ON eta.alarm_event (tag, kind) WHERE status = 'open';",
]

DOWNGRADE = [
    "DROP TABLE IF EXISTS eta.alarm_event;",
    "ALTER TABLE eta.config_sistema DROP COLUMN IF EXISTS stale_after_min;",
    "ALTER TABLE eta.config_limites DROP COLUMN IF EXISTS limite_max;",
    "ALTER TABLE eta.config_limites DROP COLUMN IF EXISTS limite_min;",
]


def upgrade() -> None:
    for stmt in UPGRADE:
        op.execute(stmt.strip().rstrip(";"))


def downgrade() -> None:
    for stmt in DOWNGRADE:
        op.execute(stmt.strip().rstrip(";"))

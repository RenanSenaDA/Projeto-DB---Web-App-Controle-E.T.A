"""sensor: faixas plausíveis (plausible_min / plausible_max)

Revision ID: 0003_sensor_plausibility
Revises: 0002_alarm_core
Create Date: 2026-06-09

Fase 2 (confiabilidade do dado): adiciona faixas de PLAUSIBILIDADE ao sensor —
valores fora delas indicam leitura provavelmente inválida (sensor com defeito,
ruído). Usadas para (a) marcar leituras "suspeitas" no painel de saúde e (b) o
worker NÃO disparar alarme em cima de leitura implausível.

Aditiva e idempotente. Ambas as colunas são opcionais (NULL = sem checagem).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0003_sensor_plausibility"
down_revision: Union[str, None] = "0002_alarm_core"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UPGRADE = [
    "ALTER TABLE eta.sensor ADD COLUMN IF NOT EXISTS plausible_min DOUBLE PRECISION;",
    "ALTER TABLE eta.sensor ADD COLUMN IF NOT EXISTS plausible_max DOUBLE PRECISION;",
]

DOWNGRADE = [
    "ALTER TABLE eta.sensor DROP COLUMN IF EXISTS plausible_max;",
    "ALTER TABLE eta.sensor DROP COLUMN IF EXISTS plausible_min;",
]


def upgrade() -> None:
    for stmt in UPGRADE:
        op.execute(stmt.strip().rstrip(";"))


def downgrade() -> None:
    for stmt in DOWNGRADE:
        op.execute(stmt.strip().rstrip(";"))

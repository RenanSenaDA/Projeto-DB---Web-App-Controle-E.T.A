from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class AlarmsIn(BaseModel):
    """Liga/desliga global dos alarmes."""
    alarms_enabled: bool


class AlarmEventOut(BaseModel):
    """Um registro do histórico de alarmes (eta.alarm_event)."""
    id: int
    tag: str
    kind: str                 # 'high' | 'low' | 'stale'
    severity: str             # 'warn' | 'crit'
    status: str               # 'open' | 'acked' | 'resolved'
    value: Optional[float] = None
    threshold: Optional[float] = None
    message: Optional[str] = None
    opened_at: datetime
    acked_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class LimitRangeIn(BaseModel):
    """Faixa de alarme de uma tag. Campos ausentes/nulos = sem aquele limite."""
    limite_min: Optional[float] = None
    limite_max: Optional[float] = None
    label: Optional[str] = None


class LimitsRangesIn(BaseModel):
    """Upsert de faixas: cada tag é substituída integralmente pelo objeto enviado."""
    ranges: Dict[str, LimitRangeIn]


class LimitRangeOut(BaseModel):
    tag: str
    limite: Optional[float] = None        # legado (limite superior) — mantido em sincronia com limite_max
    limite_min: Optional[float] = None
    limite_max: Optional[float] = None
    label: Optional[str] = None

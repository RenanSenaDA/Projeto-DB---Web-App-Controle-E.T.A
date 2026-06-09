from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SensorHealthOut(BaseModel):
    """Saúde de um sensor: última leitura, idade, status e suspeita de leitura inválida."""
    tag: str
    unit: Optional[str] = None
    last_value: Optional[float] = None
    last_ts: Optional[datetime] = None
    age_seconds: Optional[int] = None
    status: str                      # 'online' | 'stale'
    suspect: bool                    # valor fora da faixa plausível
    quality: Optional[str] = None
    plausible_min: Optional[float] = None
    plausible_max: Optional[float] = None

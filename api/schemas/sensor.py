"""
Esquemas Pydantic para sensores e medições.
"""

from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class SensorOut(BaseModel):
    """
    Esquema de saída para informações do sensor.
    """
    id: int
    tag: str
    unit: Optional[str] = None

class MeasurementPoint(BaseModel):
    """
    Esquema para um ponto de medição.
    """
    ts: datetime
    tag: str
    value: float
    unit: Optional[str] = None

class LimitsOut(BaseModel):
    """
    Esquema de saída para limites de sensores.
    """
    limits: Dict[str, float]

class LimitsIn(BaseModel):
    """
    Esquema de entrada para atualização de limites.
    """
    limits: Dict[str, float]

class AlarmsIn(BaseModel):
    """
    Esquema de entrada para configuração de alarmes.
    """
    alarms_enabled: bool
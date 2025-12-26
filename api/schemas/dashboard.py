"""
Esquemas Pydantic para o dashboard.
"""

from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

class DashboardKPI(BaseModel):
    """
    Esquema para um indicador chave de desempenho (KPI) no dashboard.
    """
    id: str
    label: str
    value: Optional[float]
    unit: Optional[str]
    limit: Optional[float] = None
    category: str = "default"
    updated_at: datetime

class DashboardOut(BaseModel):
    """
    Esquema de saída completo do dashboard.
    """
    meta: Dict[str, str]
    data: Dict[str, Dict[str, List[DashboardKPI]]]
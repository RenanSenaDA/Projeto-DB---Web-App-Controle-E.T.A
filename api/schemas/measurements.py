from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SeriesPoint(BaseModel):
    """
    Esquema otimizado para gráficos (Séries Temporais).
    Não inclui a tag, pois a tag será a chave do dicionário de retorno.
    """
    ts: datetime
    value: float
    unit: Optional[str] = None
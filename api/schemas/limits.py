from pydantic import BaseModel
from typing import Dict

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
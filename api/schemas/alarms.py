from pydantic import BaseModel

class AlarmsIn(BaseModel):
    """
    Esquema de entrada para configuração de alarmes.
    """
    alarms_enabled: bool
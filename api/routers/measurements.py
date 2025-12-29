from typing import List, Dict
from datetime import datetime, timedelta
from fastapi import APIRouter
from sqlalchemy import text
from database.connection import get_engine
from schemas.measurements import SeriesPoint 

router = APIRouter()

@router.get("/measurements/series", response_model=Dict[str, List[SeriesPoint]])
def series(tags: str, minutes: int = 60):
    """
    Recupera séries temporais de medições para os sensores especificados.
    """
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    if not tag_list:
        return {}

    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(minutes=minutes)
    
    eng = get_engine() 

    with eng.connect() as conn:
        q = text(
            """
            SELECT m.ts, s.tag, m.value, s.unit
            FROM eta.measurement m
            JOIN eta.sensor s ON s.id = m.sensor_id
            WHERE m.ts >= :start_dt AND m.ts <= :end_dt AND s.tag = ANY(:tags)
            ORDER BY s.tag, m.ts ASC;
            """
        )
        rows = conn.execute(q, {"start_dt": start_dt, "end_dt": end_dt, "tags": tag_list}).fetchall()

    # Dica de tipagem para o editor (opcional, mas bom para dev)
    data: Dict[str, List[SeriesPoint]] = {}

    for r in rows:
        tag = r._mapping["tag"]
        val = r._mapping["value"]

        data.setdefault(tag, []).append({
            "ts": r._mapping["ts"],
            "value": float(val) if val is not None else 0.0,
            "unit": r._mapping.get("unit"),
        })
        # O Pydantic (SeriesPoint) vai validar esse dicionário automaticamente na saída graças ao response_model

    return data
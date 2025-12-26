"""
Rotas do dashboard.

Fornece dados para a visualização principal do sistema, incluindo KPIs e status dos sensores.
"""

from fastapi import APIRouter
from sqlalchemy import text
from datetime import datetime
from database.connection import get_engine
from schemas.dashboard import DashboardOut, DashboardKPI

router = APIRouter()

def categorize(tag: str) -> str:
    """
    Categoriza uma tag de sensor com base em seu nome.
    """
    tl = tag.lower()
    if tl.startswith("qualidade/"): return "qualidade_da_agua"
    if any(x in tl for x in ["decantacao/", "bombeamento/", "pressao/", "nivel/"]): return "operacional"
    return "default"

@router.get("/", response_model=DashboardOut)
def get_dashboard():
    """
    Retorna os dados consolidados para o dashboard.
    
    Inclui os valores mais recentes dos sensores e seus limites configurados.
    """
    eng = get_engine()
    with eng.connect() as conn:
        last = conn.execute(text("""
            SELECT m.ts, s.tag, m.value, s.unit
            FROM eta.measurement m
            JOIN eta.sensor s ON s.id = m.sensor_id
            JOIN (SELECT sensor_id, max(ts) as ts FROM eta.measurement GROUP BY sensor_id) l 
            ON l.sensor_id = m.sensor_id AND l.ts = m.ts
        """)).fetchall()
        lim_rows = conn.execute(text("SELECT tag, limite FROM eta.config_limites")).fetchall()

    limits = {r._mapping["tag"]: float(r._mapping["limite"]) for r in lim_rows}
    kpis = []
    for r in last:
        tag = r._mapping["tag"]
        kpis.append(DashboardKPI(
            id=tag.replace("/", "_"),
            label=tag,
            value=float(r._mapping["value"]) if r._mapping["value"] is not None else None,
            unit=r._mapping.get("unit"),
            limit=limits.get(tag),
            category=categorize(tag),
            updated_at=r._mapping["ts"]
        ))
    
    return {
        "meta": {"timestamp": datetime.utcnow().isoformat(), "status": "online"},
        "data": {"eta": {"kpis": kpis}, "ultrafiltracao": {"kpis": []}, "carvao": {"kpis": []}}
    }
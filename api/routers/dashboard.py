"""
Rotas do dashboard.

Fornece dados para a visualização principal do sistema, incluindo KPIs e status dos sensores.
"""

from fastapi import APIRouter
from sqlalchemy import text
from datetime import datetime
from database.connection import get_engine
from schemas.dashboard import DashboardOut, DashboardKPI

import math
from typing import Any
import re
import unicodedata


def json_safe(obj: Any) -> Any:
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_safe(v) for v in obj]
    return obj


router = APIRouter()


def normalize_tag(tag: str) -> str:
    t = (tag or "").strip().lower()
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode("ascii")
    t = t.replace("_", "/")
    t = re.sub(r"\s+", "/", t)
    t = re.sub(r"[^a-z0-9/]+", "", t)
    t = re.sub(r"/+", "/", t)
    return t


def categorize(tag: str) -> str:
    tl = normalize_tag(tag)
    parts = tl.split("/")

    if "qualidade" in parts:
        return "qualidade"

    if "limpeza" in parts:
        return "limpeza"

    if "integridade" in parts or "alarme" in parts or "alarmes" in parts:
        return "integridade_dos_alarmes"

    if "operacional" in parts:
        return "operacional"

    if any(x in tl for x in ["decantacao", "bombeamento", "pressao", "nivel"]):
        return "operacional"

    return "default"


def get_tab(tag: str) -> str:
    """
    Define em qual ABA o KPI cai.
    - eta -> ETA
    - ultrafiltracao -> UTF/UTC
    - carvao -> FC (Filtro Carvão Ativado)
    """
    tl = normalize_tag(tag)

    # ETA
    if tl.startswith("eta/"):
        return "eta"

    # UTF / UTC (você usa UTC como prefixo hoje)
    if tl.startswith("utc/") or tl.startswith("utf/") or tl.startswith("ultrafiltracao/"):
        return "ultrafiltracao"

    # FC / Carvão
    if tl.startswith("fc/") or tl.startswith("carvao/") or "carvao" in tl or "filtro" in tl and "carvao" in tl:
        return "carvao"

    # fallback: mantém em ETA para não “sumir” KPI
    return "eta"


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
            JOIN (
                SELECT sensor_id, max(ts) as ts
                FROM eta.measurement
                GROUP BY sensor_id
            ) l ON l.sensor_id = m.sensor_id AND l.ts = m.ts
        """)).fetchall()

        lim_rows = conn.execute(
            text("SELECT tag, limite FROM eta.config_limites")
        ).fetchall()

    limits = {r._mapping["tag"]: float(r._mapping["limite"]) for r in lim_rows}

    # buckets por aba
    eta_kpis = []
    utf_kpis = []
    fc_kpis = []

    for r in last:
        tag = r._mapping["tag"]

        raw_v = r._mapping["value"]
        val = float(raw_v) if raw_v is not None else None
        if val is not None and (math.isnan(val) or math.isinf(val)):
            val = None

        kpi = DashboardKPI(
            id=tag.replace("/", "_"),
            label=tag,
            value=val,
            unit=r._mapping.get("unit"),
            limit=limits.get(tag),
            category=categorize(tag),
            updated_at=r._mapping["ts"]
        )

        tab = get_tab(tag)
        if tab == "eta":
            eta_kpis.append(kpi)
        elif tab == "ultrafiltracao":
            utf_kpis.append(kpi)
        elif tab == "carvao":
            fc_kpis.append(kpi)
        else:
            eta_kpis.append(kpi)

    return json_safe({
        "meta": {"timestamp": datetime.utcnow().isoformat(), "status": "online"},
        "data": {
            "eta": {"kpis": eta_kpis},
            "ultrafiltracao": {"kpis": utf_kpis},
            "carvao": {"kpis": fc_kpis}
        }
    })

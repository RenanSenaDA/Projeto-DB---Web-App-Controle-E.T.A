"""
Rotas de saúde dos sensores (observabilidade da ingestão).

Mostra, por sensor: última leitura, há quanto tempo, se está "mudo" (stale) e se a
leitura é "suspeita" (fora da faixa plausível). Ajuda a confiar no que o dashboard mostra.
"""
from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text

from database.connection import get_engine
from schemas.sensors import SensorHealthOut

router = APIRouter()

DEFAULT_STALE_MIN = 15


@router.get("/sensors/health", response_model=list[SensorHealthOut])
def sensors_health():
    """Estado de saúde de cada sensor (última leitura, idade, online/mudo, suspeito)."""
    eng = get_engine()
    with eng.connect() as conn:
        cfg = conn.execute(
            text("SELECT stale_after_min FROM eta.config_sistema WHERE id = 1")
        ).fetchone()
        stale_min = DEFAULT_STALE_MIN
        if cfg is not None and cfg._mapping.get("stale_after_min") is not None:
            stale_min = int(cfg._mapping["stale_after_min"])

        rows = conn.execute(text("""
            SELECT s.tag, s.unit, s.plausible_min, s.plausible_max,
                   m.value, m.ts, m.quality
            FROM eta.sensor s
            JOIN LATERAL (
                SELECT value, ts, quality
                FROM eta.measurement
                WHERE sensor_id = s.id
                ORDER BY ts DESC
                LIMIT 1
            ) m ON TRUE
            ORDER BY s.tag
        """)).fetchall()

    now = datetime.now(timezone.utc)
    out = []
    for r in rows:
        mp = r._mapping
        ts = mp["ts"]
        ts_utc = ts.replace(tzinfo=timezone.utc) if (ts is not None and ts.tzinfo is None) else ts
        age = int((now - ts_utc).total_seconds()) if ts_utc is not None else None
        stale = age is None or age > stale_min * 60

        v = mp["value"]
        pmin = mp["plausible_min"]
        pmax = mp["plausible_max"]
        suspect = v is not None and (
            (pmin is not None and v < pmin) or (pmax is not None and v > pmax)
        )

        out.append({
            "tag": mp["tag"],
            "unit": mp["unit"],
            "last_value": v,
            "last_ts": ts,
            "age_seconds": age,
            "status": "stale" if stale else "online",
            "suspect": bool(suspect),
            "quality": mp["quality"],
            "plausible_min": pmin,
            "plausible_max": pmax,
        })
    return out

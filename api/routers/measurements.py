from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Query
from sqlalchemy import text

from api.database.connection import get_engine

router = APIRouter(prefix="/measurements", tags=["Measurements"])


@router.get("/series")
def measurements_series(
    tags: List[str] = Query(..., description="Lista de tags. Pode repetir ?tags=... ou enviar uma string com tags separadas por vírgula."),
    minutes: int = Query(60, ge=1, le=60 * 24 * 30, description="Janela em minutos (máx. 30 dias)"),
) -> Dict[str, Any]:
    """
    Retorna séries temporais para as tags solicitadas, dentro da janela de tempo (minutes).

    Formato:
      {
        "minutes": 60,
        "series": {
          "tag1": [{"ts": "...", "value": 1.23}, ...],
          "tag2": [{"ts": "...", "value": 4.56}, ...]
        }
      }
    """

    # Se veio 1 item contendo tags separadas por vírgula, normaliza
    if len(tags) == 1 and "," in tags[0]:
        tags = [t.strip() for t in tags[0].split(",") if t.strip()]

    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    # Usa schema eta.measurement conforme seu banco
    stmt = text(
        """
        SELECT tag, ts, value
        FROM eta.measurement
        WHERE tag = ANY(:tags)
          AND ts >= :since
        ORDER BY ts ASC
        """
    )

    engine = get_engine()

    series: Dict[str, List[Dict[str, Any]]] = {t: [] for t in tags}

    with engine.connect() as conn:
        rows = conn.execute(stmt, {"tags": tags, "since": since}).fetchall()

    for tag, ts, value in rows:
        # normaliza timestamp para ISO
        if isinstance(ts, datetime) and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        series.setdefault(tag, []).append(
            {"ts": ts.isoformat() if isinstance(ts, datetime) else str(ts), "value": value}
        )

    return {"minutes": minutes, "series": series}

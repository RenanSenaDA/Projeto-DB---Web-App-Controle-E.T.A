from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from database.connection import get_engine
from deps import get_current_user
from schemas.alarms import AlarmsIn, AlarmEventOut, LimitsRangesIn, LimitRangeOut

router = APIRouter()

@router.get("/alarms/status")
def alarms_status():
    """
    Verifica o estado global do sistema de alarmes (Ativado/Desativado).
    Se a configuração não existir na base de dados, assume 'True' por omissão.
    """
    eng = get_engine()
    with eng.connect() as conn:
        row = conn.execute(text("SELECT alarms_enabled FROM eta.config_sistema WHERE id=1;")).fetchone()
    
    return {"alarms_enabled": bool(row._mapping["alarms_enabled"]) if row else True}

@router.put("/alarms/status")
def set_alarms(payload: AlarmsIn):
    """
    Altera o estado global dos alarmes.
    Permite silenciar todo o sistema durante manutenções para evitar spam de e-mails.
    """
    eng = get_engine()
    with eng.begin() as conn:
        # Tenta atualizar o registo existente
        result = conn.execute(text("""
            UPDATE eta.config_sistema 
            SET alarms_enabled = :v, updated_at = now() 
            WHERE id = 1;
        """), {"v": bool(payload.alarms_enabled)})
        
        # Se o registo ID=1 não existir, cria-o
        if result.rowcount == 0:
            conn.execute(text("""
                INSERT INTO eta.config_sistema (id, alarms_enabled) VALUES (1, :v)
            """), {"v": bool(payload.alarms_enabled)})

    return {"ok": True}


@router.get("/alarms/events", response_model=list[AlarmEventOut])
def list_alarm_events(status: Optional[str] = None, limit: int = 100):
    """
    Histórico de alarmes (eta.alarm_event), mais recentes primeiro.
    Filtro opcional por status: open | acked | resolved.
    """
    limit = max(1, min(limit, 500))
    where = ""
    params = {"lim": limit}
    if status:
        where = "WHERE status = :st"
        params["st"] = status

    eng = get_engine()
    with eng.connect() as conn:
        rows = conn.execute(text(f"""
            SELECT id, tag, kind, severity, status, value, threshold, message,
                   opened_at, acked_at, resolved_at
            FROM eta.alarm_event
            {where}
            ORDER BY opened_at DESC
            LIMIT :lim
        """), params).fetchall()

    return [dict(r._mapping) for r in rows]


@router.post("/alarms/events/{event_id}/ack")
def ack_alarm_event(event_id: int, user_id: int = Depends(get_current_user)):
    """
    Reconhece (acknowledge) um alarme: registra quem reconheceu e quando.
    Só muda o status para 'acked' se ainda estiver 'open'.
    """
    eng = get_engine()
    with eng.begin() as conn:
        res = conn.execute(text("""
            UPDATE eta.alarm_event
            SET status   = CASE WHEN status = 'open' THEN 'acked' ELSE status END,
                acked_by = :uid,
                acked_at = now()
            WHERE id = :id
        """), {"uid": user_id, "id": event_id})
        if res.rowcount == 0:
            raise HTTPException(status_code=404, detail="Alarme não encontrado.")
    return {"ok": True}


@router.get("/alarms/limits", response_model=list[LimitRangeOut])
def get_alarm_limits():
    """Faixas de alarme por tag (limite_min/limite_max/label + `limite` legado)."""
    eng = get_engine()
    with eng.connect() as conn:
        rows = conn.execute(text("""
            SELECT tag, limite, limite_min, limite_max, label
            FROM eta.config_limites
            ORDER BY tag
        """)).fetchall()
    return [dict(r._mapping) for r in rows]


@router.put("/alarms/limits")
def put_alarm_limits(payload: LimitsRangesIn, user_id: int = Depends(get_current_user)):
    """
    Upsert das faixas de alarme. Cada tag é substituída integralmente pelo objeto
    enviado (min/max/label). `limite` legado fica em sincronia com `limite_max`.
    """
    if not payload.ranges:
        raise HTTPException(status_code=400, detail="O payload não pode estar vazio.")

    eng = get_engine()
    with eng.begin() as conn:
        for tag, rg in payload.ranges.items():
            conn.execute(text("""
                INSERT INTO eta.config_limites (tag, limite, limite_min, limite_max, label, updated_at)
                VALUES (:tag, :lmax, :lmin, :lmax, :label, now())
                ON CONFLICT (tag) DO UPDATE SET
                    limite_min = EXCLUDED.limite_min,
                    limite_max = EXCLUDED.limite_max,
                    limite     = EXCLUDED.limite_max,
                    label      = EXCLUDED.label,
                    updated_at = now()
            """), {"tag": tag, "lmin": rg.limite_min, "lmax": rg.limite_max, "label": rg.label})

    return {"ok": True, "updated_count": len(payload.ranges)}
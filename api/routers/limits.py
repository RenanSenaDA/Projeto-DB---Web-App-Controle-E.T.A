from typing import Dict
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from database.connection import get_engine
from schemas.limits import LimitsOut, LimitsIn 

router = APIRouter()

@router.get("/limits", response_model=LimitsOut)
def get_limits():
    """
    Retorna todos os limites configurados no sistema.
    Utilizado para preencher a tabela de configuração de limites no Frontend.
    """
    eng = get_engine()
    with eng.connect() as conn:
        rows = conn.execute(text("SELECT tag, limite FROM eta.config_limites;")).fetchall()
    
    limits: Dict[str, float] = {}
    for r in rows:
        try:
            limits[r._mapping["tag"]] = float(r._mapping["limite"])
        except Exception:
            continue
    return {"limits": limits}

@router.put("/limits")
def put_limits(payload: LimitsIn):
    """
    Atualiza limites operacionais.
    
    Suporta tanto atualização em massa (vários itens) como atualização individual.
    Utiliza lógica de UPSERT (Update or Insert) baseada na tag do sensor.
    """
    if not payload.limits:
        raise HTTPException(status_code=400, detail="O payload não pode estar vazio.")

    eng = get_engine()
    with eng.begin() as conn:
        for tag, lim in payload.limits.items():
            conn.execute(text("""
                INSERT INTO eta.config_limites(tag, limite)
                VALUES (:tag, :limite)
                ON CONFLICT(tag) 
                DO UPDATE SET 
                    limite = EXCLUDED.limite, 
                    updated_at = now();
            """), {"tag": tag, "limite": float(lim)})
            
    return {"ok": True, "updated_count": len(payload.limits)}
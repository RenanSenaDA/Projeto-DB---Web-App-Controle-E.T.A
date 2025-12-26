"""
Rotas para geração de relatórios.
"""

from fastapi import APIRouter
from datetime import datetime, timedelta, date
from typing import Optional
from services.report_service import generate_excel_report   

router = APIRouter()

@router.get("/excel")
def report_excel(period: str = "ultimos_7_dias"):
    """
    Gera relatório Excel pré-definido por período.
    
    Args:
        period (str): 'ultimos_30_dias', 'ultimo_1_dia', ou 'ultimos_7_dias' (padrão).
    """
    now = datetime.utcnow()
    days = 30 if period == "ultimos_30_dias" else 1 if period == "ultimo_1_dia" else 7
    start = now - timedelta(days=days)
    return generate_excel_report(start, now, filename=f"relatorio_{period}.xlsx")

@router.get("/excel-range")
def report_excel_range(start: date, end: date, tags: Optional[str] = None):
    """
    Gera relatório Excel personalizado por intervalo de datas e tags.
    
    Args:
        start (date): Data inicial.
        end (date): Data final.
        tags (str, optional): Lista de tags separadas por vírgula.
    """
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end + timedelta(days=1), datetime.min.time())
    tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
    return generate_excel_report(start_dt, end_dt, tags=tag_list if tag_list else None, filename=f"relatorio_{start}_{end}.xlsx")
"""
Módulo de serviço de relatórios.

Gera relatórios em Excel a partir de dados históricos de medições.
"""

import io
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, List
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from core.config import settings
from database.connection import get_engine

def _sanitize_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpa e formata o DataFrame de medições.
    Converte timestamps para fuso horário local e valores para numérico.
    """
    if df.empty: return df
    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce").dt.tz_convert(settings.LOCAL_TZ).dt.tz_localize(None)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna(subset=["ts", "value"]).sort_values("ts")

def _autosize(ws, data: pd.DataFrame):
    """
    Ajusta automaticamente a largura das colunas do Excel.
    """
    for i, col in enumerate(data.columns):
        try:
            max_len = max(len(str(col)), *(data[col].astype(str).map(len).tolist()))
        except:
            max_len = 18
        ws.set_column(i, i, min(max_len + 2, 40))

def generate_excel_report(start_dt: datetime, end_dt: datetime, tags: Optional[List[str]] = None, filename: str = "relatorio.xlsx"):
    """
    Gera um relatório Excel com dados de medições no período especificado.

    Args:
        start_dt (datetime): Data/hora de início.
        end_dt (datetime): Data/hora de fim.
        tags (Optional[List[str]]): Lista de tags de sensores para filtrar.
        filename (str): Nome do arquivo de saída.

    Returns:
        StreamingResponse: Resposta HTTP contendo o arquivo Excel.
    """
    eng = get_engine()
    with eng.connect() as conn:
        query_str = """
            SELECT m.ts, s.tag, m.value, s.unit, m.quality, m.meta
            FROM eta.measurement m
            JOIN eta.sensor s ON s.id = m.sensor_id
            WHERE m.ts >= :start_dt AND m.ts < :end_dt
        """
        if tags:
            query_str += " AND s.tag = ANY(:tags)"
        query_str += " ORDER BY m.ts ASC;"
        
        params = {"start_dt": start_dt, "end_dt": end_dt}
        if tags: params["tags"] = tags
        
        rows = conn.execute(text(query_str), params).fetchall()
        
    df = pd.DataFrame(rows, columns=["ts", "tag", "value", "unit", "quality", "meta"]) if rows else pd.DataFrame(columns=["ts","tag","value","unit","quality","meta"])
    df = _sanitize_df(df)
    
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter", datetime_format="yyyy-mm-dd HH:MM:SS") as xw:
        if df.empty:
            pd.DataFrame({"aviso": ["Sem dados."]}).to_excel(xw, sheet_name="Resumo", index=False)
        else:
            df["data"] = df["ts"].dt.date
            df["hora"] = df["ts"].dt.floor("h")

            # Lógica de agregação (mantida original)
            last = df.sort_values("ts").groupby("tag", as_index=False).tail(1)
            resumo = (df.groupby("tag").agg(**{"Qtd": ("value", "count"), "media": ("value", "mean"), "min": ("value", "min"), "max": ("value", "max")})
                      .reset_index().merge(last[["tag", "value", "ts", "unit"]], on="tag", how="left")
                      .rename(columns={"value": "ultimo_valor", "ts": "ultimo_ts"}))
            
            seconds = max(0, int((end_dt - start_dt).total_seconds()))
            esperado = max(1, seconds // settings.FEED_INTERVAL)
            resumo["completude_%"] = (resumo["Qtd"] / esperado * 100).clip(upper=100).round(1)

            resumo.to_excel(xw, sheet_name="Resumo", index=False)
            df.groupby(["tag", "data"], as_index=False).agg(media=("value", "mean")).to_excel(xw, sheet_name="Diario", index=False)
            df.groupby(["tag", "hora"], as_index=False).agg(media=("value", "mean")).to_excel(xw, sheet_name="Horario", index=False)
            df[["ts", "tag", "unit", "value", "quality", "meta"]].sort_values("ts").to_excel(xw, sheet_name="Bruto", index=False)

            for s in xw.sheets.values(): _autosize(s, df) # Simplificado para exemplo

    buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename={filename}"})
"""
Módulo de serviço de relatórios.

Gera relatórios em Excel a partir de dados históricos de medições.
Melhorias:
- Aba Resumo com colunas: Estação, Categoria, Indicador, Tag, Qtd, Média, Mín, Máx, Último valor, Última leitura, Unit, Amplitude (%)
- Formatação (header, freeze, filtros, zebra)
- Datas e números formatados (evita ########)
"""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import List, Optional, Tuple

import pandas as pd
from fastapi.responses import StreamingResponse
from sqlalchemy import text

from database.connection import get_engine


# ----------------------------
# Helpers
# ----------------------------
def _split_tag(tag: str) -> Tuple[str, str, str]:
    """
    tag esperada: "<estacao>/<categoria>/<nome...>"
    exemplo: "eta/operacional/Fluxo Alimentação M3/h"
    """
    raw = str(tag or "").strip()
    parts = [p.strip() for p in raw.split("/") if p.strip()]
    station = parts[0] if len(parts) >= 1 else ""
    category = parts[1] if len(parts) >= 2 else ""
    indicator = "/".join(parts[2:]) if len(parts) >= 3 else raw
    return station, category, indicator


def _safe_upper_station(st: str) -> str:
    # Mantém acentos se existirem; se vier "ultrafiltracao" e "carvao",
    # você pode mapear aqui futuramente (se quiser).
    return (st or "").strip().upper()


def _autosize_worksheet(ws, df: pd.DataFrame, min_w: int = 10, max_w: int = 60) -> None:
    """
    Ajusta largura das colunas com base no conteúdo.
    """
    for i, col in enumerate(df.columns):
        series = df[col].astype(str).fillna("")
        max_len = max([len(str(col))] + series.map(len).tolist())
        width = max(min_w, min(max_w, max_len + 2))
        ws.set_column(i, i, width)


def _apply_table_style(workbook, worksheet, df: pd.DataFrame, *, freeze_row: int = 1, freeze_col: int = 0) -> None:
    """
    Aplica estilo de tabela:
    - Cabeçalho formatado
    - Freeze
    - Autofilter
    - Zebra (linhas alternadas)
    """
    header_fmt = workbook.add_format(
        {
            "bold": True,
            "font_color": "white",
            "bg_color": "#1F4E79",
            "border": 1,
            "align": "center",
            "valign": "vcenter",
        }
    )
    row_even = workbook.add_format({"bg_color": "#F4F7FB"})
    row_odd = workbook.add_format({"bg_color": "#FFFFFF"})

    # Header (linha 0)
    worksheet.set_row(0, 22, header_fmt)

    # Freeze panes
    worksheet.freeze_panes(freeze_row, freeze_col)

    # Autofilter
    if df.shape[1] > 0:
        worksheet.autofilter(0, 0, max(0, len(df)), df.shape[1] - 1)

    # Zebra (a partir da linha 1)
    if len(df) > 0:
        for r in range(1, len(df) + 1):
            worksheet.set_row(r, 18, row_even if r % 2 == 0 else row_odd)


def _excel_safe_datetimes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Excel não suporta datetimes com timezone (tz-aware).
    Converte para UTC e remove tz (vira tz-naive).
    """
    if df is None or df.empty:
        return df

    # Colunas datetime tz-aware
    tz_cols = df.select_dtypes(include=["datetimetz"]).columns
    for c in tz_cols:
        # Converte para UTC e remove tz
        df[c] = df[c].dt.tz_convert("UTC").dt.tz_localize(None)

    # Índice tz-aware
    if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None:
        df.index = df.index.tz_convert("UTC").tz_localize(None)

    return df


# ----------------------------
# Main generator
# ----------------------------
def generate_excel_report(
    start_dt: datetime,
    end_dt: datetime,
    tags: Optional[List[str]] = None,
    filename: str = "relatorio.xlsx",
):
    """
    Gera um relatório Excel com dados de medições no período especificado.

    Args:
        start_dt: datetime início (inclusive)
        end_dt: datetime fim (inclusive)
        tags: lista opcional de tags para filtrar
        filename: nome do arquivo para download

    Returns:
        StreamingResponse com o arquivo Excel.
    """
    eng = get_engine()

    sql = """
        SELECT
            m.ts,
            s.tag,
            s.unit,
            m.value,
            m.quality,
            m.meta
        FROM eta.measurement m
        JOIN eta.sensor s ON s.id = m.sensor_id
        WHERE m.ts >= :start AND m.ts <= :end
    """

    params = {"start": start_dt, "end": end_dt}

    if tags:
        sql += " AND s.tag = ANY(:tags)"
        params["tags"] = tags

    sql += " ORDER BY m.ts ASC"

    with eng.connect() as conn:
        rows = conn.execute(text(sql), params).fetchall()

    buf = BytesIO()

    # Sem dados
    if not rows:
        aviso_df = pd.DataFrame({"aviso": ["Sem dados para o período selecionado."]})
        with pd.ExcelWriter(buf, engine="xlsxwriter") as xw:
            aviso_df.to_excel(xw, sheet_name="Resumo", index=False)
            wb = xw.book
            ws = xw.sheets["Resumo"]
            _autosize_worksheet(ws, aviso_df)
            ws.set_row(0, 22, wb.add_format({"bold": True, "bg_color": "#1F4E79", "font_color": "white"}))

        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    # DataFrame bruto
    df = pd.DataFrame([dict(r._mapping) for r in rows])

    # ts pode vir tz-aware (TIMESTAMPTZ). Excel NÃO suporta tz-aware.
    df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
    if pd.api.types.is_datetime64tz_dtype(df["ts"]):
        df["ts"] = df["ts"].dt.tz_convert("UTC").dt.tz_localize(None)

    # Deriva colunas de leitura (estacao/categoria/indicador)
    derived = df["tag"].apply(lambda t: pd.Series(_split_tag(t), index=["estacao", "categoria", "indicador"]))
    df = pd.concat([df, derived], axis=1)
    df["estacao"] = df["estacao"].apply(_safe_upper_station)

    # Preparação para agrupamentos
    df["data"] = df["ts"].dt.date
    df["hora"] = df["ts"].dt.floor("h")  # "H" deprecated -> use "h"

    # ----------------------------
    # RESUMO (bonito e útil)
    # ----------------------------
    agg_base = (
        df.groupby(["estacao", "categoria", "indicador", "tag", "unit"], as_index=False)
        .agg(
            qtd=("value", "count"),
            media=("value", "mean"),
            min=("value", "min"),
            max=("value", "max"),
        )
    )

    last_rows = (
        df.sort_values("ts")
        .groupby("tag", as_index=False)
        .tail(1)[["tag", "value", "ts"]]
        .rename(columns={"value": "ultimo_valor", "ts": "ultimo_ts"})
    )

    resumo = agg_base.merge(last_rows, on="tag", how="left")
    resumo["amplitude_%"] = ((resumo["max"] - resumo["min"]) / resumo["media"].replace(0, pd.NA)) * 100
    resumo["amplitude_%"] = resumo["amplitude_%"].fillna(0)

    resumo = resumo.sort_values(["estacao", "categoria", "indicador"]).reset_index(drop=True)

    resumo = resumo[
        [
            "tag",
            "estacao",
            "categoria",
            "indicador",
            "qtd",
            "media",
            "min",
            "max",
            "ultimo_valor",
            "ultimo_ts",
            "unit",
            "amplitude_%",
        ]
    ].rename(
        columns={
            "qtd": "Qtd",
            "media": "Média",
            "min": "Mín",
            "max": "Máx",
            "ultimo_valor": "Último valor",
            "ultimo_ts": "Última leitura",
            "unit": "Unidade",
            "amplitude_%": "Amplitude (%)",
            "tag": "Tag",
            "estacao": "Estação",
            "categoria": "Categoria",
            "indicador": "Indicador",
        }
    )

    # ----------------------------
    # DIÁRIO / HORÁRIO / BRUTO
    # ----------------------------
    diario = (
        df.groupby(["estacao", "categoria", "indicador", "tag", "data"], as_index=False)
        .agg(media=("value", "mean"), min=("value", "min"), max=("value", "max"), qtd=("value", "count"))
        .rename(columns={"data": "Data", "media": "Média", "min": "Mín", "max": "Máx", "qtd": "Qtd"})
        .sort_values(["estacao", "categoria", "indicador", "tag", "Data"])
        .reset_index(drop=True)
    )

    horario = (
        df.groupby(["estacao", "categoria", "indicador", "tag", "hora"], as_index=False)
        .agg(media=("value", "mean"), min=("value", "min"), max=("value", "max"), qtd=("value", "count"))
        .rename(columns={"hora": "Hora", "media": "Média", "min": "Mín", "max": "Máx", "qtd": "Qtd"})
        .sort_values(["estacao", "categoria", "indicador", "tag", "Hora"])
        .reset_index(drop=True)
    )

    bruto = (
        df[["ts", "estacao", "categoria", "indicador", "tag", "unit", "value", "quality"]]
        .rename(
            columns={
                "ts": "Timestamp",
                "unit": "Unidade",
                "value": "Valor",
                "quality": "Qualidade",
                "tag": "Tag",
                "estacao": "Estação",
                "categoria": "Categoria",
                "indicador": "Indicador",
            }
        )
        .sort_values("Timestamp")
        .reset_index(drop=True)
    )

    # Excel-safe: remove timezone de qualquer coluna datetime tz-aware
    resumo = _excel_safe_datetimes(resumo)
    diario = _excel_safe_datetimes(diario)
    horario = _excel_safe_datetimes(horario)
    bruto = _excel_safe_datetimes(bruto)

    # ----------------------------
    # Escreve Excel com formatação
    # ----------------------------
    with pd.ExcelWriter(
        buf,
        engine="xlsxwriter",
        datetime_format="dd/mm/yyyy hh:mm",
        date_format="dd/mm/yyyy",
    ) as xw:
        resumo.to_excel(xw, sheet_name="Resumo", index=False)
        diario.to_excel(xw, sheet_name="Diário", index=False)
        horario.to_excel(xw, sheet_name="Horário", index=False)
        bruto.to_excel(xw, sheet_name="Bruto", index=False)

        wb = xw.book

        # formats numéricos
        fmt_int = wb.add_format({"num_format": "0"})
        fmt_2 = wb.add_format({"num_format": "0.00"})
        fmt_pct = wb.add_format({"num_format": "0.00%"})
        fmt_dt = wb.add_format({"num_format": "dd/mm/yyyy hh:mm"})
        fmt_date = wb.add_format({"num_format": "dd/mm/yyyy"})

        # ----- Resumo -----
        ws = xw.sheets["Resumo"]
        _autosize_worksheet(ws, resumo, min_w=10, max_w=70)
        _apply_table_style(wb, ws, resumo, freeze_row=1, freeze_col=1)

        # Ajustes finos de colunas (Resumo)
        ws.set_column(0, 0, 45)  # Tag
        ws.set_column(1, 2, 16)  # Estação, Categoria
        ws.set_column(3, 3, 40)  # Indicador

        ws.set_column(4, 4, 8, fmt_int)   # Qtd
        ws.set_column(5, 8, 14, fmt_2)    # Média, Mín, Máx, Último valor
        ws.set_column(9, 9, 20, fmt_dt)   # Última leitura
        ws.set_column(10, 10, 10)         # Unidade

        # Amplitude (%) (11) -> valor no DF é "percentual" (ex: 12.34), converte para fração (0.1234)
        if len(resumo) > 0:
            amp_col_idx = 11
            amp_vals = (resumo["Amplitude (%)"].astype(float) / 100.0).tolist()
            ws.write_column(1, amp_col_idx, amp_vals, fmt_pct)
        ws.set_column(11, 11, 14, fmt_pct)

        # ----- Diário -----
        ws = xw.sheets["Diário"]
        _autosize_worksheet(ws, diario, min_w=10, max_w=70)
        _apply_table_style(wb, ws, diario, freeze_row=1, freeze_col=0)
        if "Data" in diario.columns:
            idx = list(diario.columns).index("Data")
            ws.set_column(idx, idx, 12, fmt_date)

        # ----- Horário -----
        ws = xw.sheets["Horário"]
        _autosize_worksheet(ws, horario, min_w=10, max_w=70)
        _apply_table_style(wb, ws, horario, freeze_row=1, freeze_col=0)
        if "Hora" in horario.columns:
            idx = list(horario.columns).index("Hora")
            ws.set_column(idx, idx, 18, fmt_dt)

        # ----- Bruto -----
        ws = xw.sheets["Bruto"]
        _autosize_worksheet(ws, bruto, min_w=10, max_w=70)
        _apply_table_style(wb, ws, bruto, freeze_row=1, freeze_col=0)
        if "Timestamp" in bruto.columns:
            idx = list(bruto.columns).index("Timestamp")
            ws.set_column(idx, idx, 20, fmt_dt)
        if "Valor" in bruto.columns:
            idx = list(bruto.columns).index("Valor")
            ws.set_column(idx, idx, 14, fmt_2)
        if "Tag" in bruto.columns:
            idx = list(bruto.columns).index("Tag")
            ws.set_column(idx, idx, 45)

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


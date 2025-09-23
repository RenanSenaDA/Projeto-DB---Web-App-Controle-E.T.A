# worker/report_monthly.py
import os, io, argparse
from datetime import date
import pandas as pd
from sqlalchemy import create_engine, text

LOCAL_TZ = os.getenv("LOCAL_TZ", "America/Fortaleza")
FEED_INTERVAL = int(os.getenv("FEED_INTERVAL", "5"))

def month_bounds_local_to_utc(year: int, month: int):
    start_local = pd.Timestamp(year=year, month=month, day=1, tz=LOCAL_TZ)
    end_local = (start_local + pd.offsets.MonthBegin(1))
    return start_local.tz_convert("UTC").to_pydatetime(), end_local.tz_convert("UTC").to_pydatetime()

def fetch_period(db_url, start_utc, end_utc):
    eng = create_engine(db_url, pool_pre_ping=True)
    with eng.connect() as c:
        q = text("""
            SELECT m.ts, s.tag, m.value, s.unit, m.quality, m.meta
            FROM eta.measurement m
            JOIN eta.sensor s ON s.id = m.sensor_id
            WHERE m.ts >= :start_dt AND m.ts < :end_dt
            ORDER BY m.ts ASC;
        """)
        df = pd.read_sql(q, c, params={"start_dt": start_utc, "end_dt": end_utc})
    df["ts"] = (pd.to_datetime(df["ts"], utc=True)
                .dt.tz_convert(LOCAL_TZ).dt.tz_localize(None))
    return df

def _autosize(ws, df):
    for i, col in enumerate(df.columns):
        try:
            max_len = max(len(str(col)), *(df[col].astype(str).str.len().tolist()))
        except Exception:
            max_len = 18
        ws.set_column(i, i, min(max_len + 2, 40))

def build_excel(df, month_label):
    import xlsxwriter  # garante que o pacote está disponível
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter", datetime_format="yyyy-mm-dd HH:MM:SS") as xw:
        if df.empty:
            out = pd.DataFrame({"aviso":[f"Sem dados para {month_label}."]})
            out.to_excel(xw, sheet_name="Resumo", index=False)
            _autosize(xw.sheets["Resumo"], out)
            return buf.getvalue()

        df["data"] = df["ts"].dt.date
        df["hora"] = df["ts"].dt.floor("h")

        last = df.sort_values("ts").groupby("tag", as_index=False).tail(1)
        resumo = (df.groupby("tag").agg(pontos=("value","count"),
                                        media=("value","mean"),
                                        minimo=("value","min"),
                                        maximo=("value","max")).reset_index()
                  .merge(last[["tag","value","ts","unit"]], on="tag", how="left")
                 ).rename(columns={"value":"ultimo_valor","ts":"ultimo_ts","unit":"unidade"})

        # completude (aprox.) em relação ao mês inteiro
        # obs: se gerar para um mês ainda em curso, o % será baixo por design
        total_seconds = (pd.Timestamp(resumo["ultimo_ts"].max()) - pd.Timestamp(df["ts"].min())).total_seconds()
        esperado = max(1, int(total_seconds // FEED_INTERVAL))
        resumo["completude_%"] = (resumo["pontos"]/esperado*100).clip(upper=100).round(1)

        diario = (df.groupby(["tag","data"], as_index=False)
                    .agg(pontos=("value","count"), media=("value","mean"),
                         minimo=("value","min"), maximo=("value","max"))
                    .sort_values(["tag","data"]))
        horario = (df.groupby(["tag","hora"], as_index=False)
                    .agg(pontos=("value","count"), media=("value","mean"),
                         minimo=("value","min"), maximo=("value","max"))
                    .sort_values(["tag","hora"]))
        bruto = df[["ts","tag","unit","value","quality","meta"]].sort_values("ts")

        resumo.to_excel(xw, sheet_name="Resumo", index=False)
        diario.to_excel(xw, sheet_name="Diario", index=False)
        horario.to_excel(xw, sheet_name="Horario", index=False)
        bruto.to_excel(xw, sheet_name="Bruto", index=False)

        for name, data in [("Resumo", resumo), ("Diario", diario), ("Horario", horario), ("Bruto", bruto)]:
            ws = xw.sheets[name]
            ws.freeze_panes(1, 1)
            _autosize(ws, data)
    return buf.getvalue()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=date.today().year)
    ap.add_argument("--month", type=int, default=(date.today().replace(day=1) - pd.offsets.MonthBegin(1)).month)
    ap.add_argument("--outdir", type=str, default="./reports")
    args = ap.parse_args()

    host = os.getenv("PGHOST","localhost")
    port = os.getenv("PGPORT","5432")
    user = os.getenv("PGUSER","postgres")
    pwd  = os.getenv("PGPASSWORD","postgres")
    db   = os.getenv("PGDATABASE","eta")
    db_url = f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"

    start_utc, end_utc = month_bounds_local_to_utc(args.year, args.month)
    df = fetch_period(db_url, start_utc, end_utc)
    data = build_excel(df, f"{args.month:02d}/{args.year}")

    os.makedirs(args.outdir, exist_ok=True)
    fname = os.path.join(args.outdir, f"relatorio_ETA_{args.year}-{args.month:02d}.xlsx")
    with open(fname, "wb") as f:
        f.write(data)
    print(f"OK: {fname}")

if __name__ == "__main__":
    main()

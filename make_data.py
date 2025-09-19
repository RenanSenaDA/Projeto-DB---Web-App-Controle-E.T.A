# make_data.py
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone

# 30 dias de dados a cada 15 minutos
start = datetime.now(timezone.utc) - timedelta(days=30)
end = datetime.now(timezone.utc)
ts = pd.date_range(start=start, end=end, freq="15min", inclusive="left")

rng = np.random.default_rng(42)

def diurnal_cycle(n, amplitude=1.0, phase=0.0):
    # ciclo diário (24h) aproximado para 15min
    x = np.linspace(0 + phase, 2*np.pi * (n / (24*4)), n)
    return amplitude * np.sin(x)

N = len(ts)
signals = {
    ("qualidade/ph", "pH"):            {"base": 7.2,  "noise": 0.06, "drift": 0.0,     "amp": 0.08},
    ("decantacao/turbidez", "NTU"):    {"base": 0.3,  "noise": 0.05, "drift": 0.0,     "amp": 0.07},
    ("bombeamento/vazao", "m3/h"):     {"base": 160., "noise": 8.0,  "drift": 0.0,     "amp": 30.0},
    ("qualidade/cloro", "mg/L"):       {"base": 1.8,  "noise": 0.12, "drift": -0.0005, "amp": 0.2},
    ("pressao/linha1", "bar"):         {"base": 3.2,  "noise": 0.08, "drift": 0.0002,  "amp": 0.25},
    ("nivel/reservatorio", "%"):       {"base": 65.,  "noise": 2.0,  "drift": 0.01,    "amp": 8.0},
}

rows = []
for (tag, unit), cfg in signals.items():
    base  = cfg["base"]
    noise = cfg["noise"]
    drift = cfg["drift"]
    amp   = cfg["amp"]

    cycle = diurnal_cycle(N, amplitude=amp)
    noise_series = rng.normal(0, noise, N)
    drift_series = np.linspace(0, drift*N, N)
    values = base + cycle + noise_series + drift_series

    # limites físicos básicos
    if unit == "NTU":  values = np.clip(values, 0.02, 5.0)
    if unit == "pH":   values = np.clip(values, 6.4, 8.8)
    if unit == "mg/L": values = np.clip(values, 0.2, 4.0)
    if unit == "bar":  values = np.clip(values, 1.0, 6.0)
    if unit == "%":    values = np.clip(values, 5.0, 100.0)
    if unit == "m3/h": values = np.clip(values, 20.0, 400.0)

    # algumas anomalias
    idx = rng.choice(N, size=6, replace=False)
    values[idx] *= rng.uniform(0.6, 1.4, size=6)

    for t, v in zip(ts, values):
        rows.append({
            "ts": t.isoformat(),
            "tag": tag,
            "value": float(np.round(v, 3)),
            "unit": unit,
            "quality": True,
            "meta": json.dumps({"sim": True}, ensure_ascii=False)
        })

df = pd.DataFrame(rows).sort_values("ts")

# salva na PASTA ATUAL (sem /mnt/data)
df.to_csv("eta_synthetic_month_long.csv", index=False)
wide = df.pivot_table(index="ts", columns="tag", values="value").reset_index()
wide.to_csv("eta_synthetic_month_wide.csv", index=False)

print("Arquivos gerados: eta_synthetic_month_long.csv e eta_synthetic_month_wide.csv")

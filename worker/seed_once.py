# worker/seed_once.py
import os, math, random
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, text

# --------- Config DB (envs ou defaults locais) ----------
PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = os.getenv("PGPORT", "5432")
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD", "postgres")
PGDATABASE = os.getenv("PGDATABASE", "eta")
DB_URL = os.getenv(
    "DB_URL",
    f"postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}",
)

# --------- Janela e granularidade do seed ----------
HOURS_BACK = int(os.getenv("SEED_HOURS", "2"))          # últimas 2h
STEP_SECONDS = int(os.getenv("SEED_STEP_SECONDS", "30"))# um ponto a cada 30s

# --------- Tags e unidades ----------
TAGS = [
    "qualidade/ph",
    "decantacao/turbidez",
    "bombeamento/vazao",
    "qualidade/cloro",
    "pressao/linha1",
    "nivel/reservatorio",
]
UNITS = {
    "qualidade/ph": "pH",
    "decantacao/turbidez": "NTU",
    "bombeamento/vazao": "m³/h",
    "qualidade/cloro": "mg/L",
    "pressao/linha1": "bar",
    "nivel/reservatorio": "m",
}

# --------- DDL / bootstrap ----------
DDL_SCHEMA = "CREATE SCHEMA IF NOT EXISTS eta;"
DDL_SENSOR = """
CREATE TABLE IF NOT EXISTS eta.sensor (
  id   SERIAL PRIMARY KEY,
  tag  TEXT NOT NULL UNIQUE,
  unit TEXT,
  meta JSONB
);
"""
DDL_MEAS = """
CREATE TABLE IF NOT EXISTS eta.measurement (
  id         BIGSERIAL PRIMARY KEY,
  sensor_id  INTEGER NOT NULL REFERENCES eta.sensor(id) ON DELETE CASCADE,
  ts         TIMESTAMPTZ NOT NULL,
  value      DOUBLE PRECISION NOT NULL,
  quality    TEXT,
  meta       JSONB,
  CONSTRAINT uq_sensor_ts UNIQUE(sensor_id, ts)
);
"""
IDX1 = "CREATE INDEX IF NOT EXISTS ix_measurement_ts ON eta.measurement(ts);"
IDX2 = "CREATE INDEX IF NOT EXISTS ix_measurement_sensor_ts ON eta.measurement(sensor_id, ts DESC);"

def ensure_db(engine):
    with engine.begin() as conn:
        conn.execute(text(DDL_SCHEMA))
        conn.execute(text(DDL_SENSOR))
        conn.execute(text(DDL_MEAS))
        conn.execute(text(IDX1))
        conn.execute(text(IDX2))
        # sensores padrão
        for tag in TAGS:
            conn.execute(
                text("""
                    INSERT INTO eta.sensor(tag, unit)
                    VALUES (:tag, :unit)
                    ON CONFLICT (tag) DO NOTHING;
                """),
                {"tag": tag, "unit": UNITS.get(tag)},
            )

def map_tag_to_id(engine):
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT id, tag FROM eta.sensor")).fetchall()
    return {tag: sid for (sid, tag) in rows}

# --------- Geradores sintéticos por tag ----------
def synth_value(tag: str, i: int) -> float:
    """Gera valor plausível por tag (base + seno + ruído). i = índice do ponto."""
    # período maior → variação lenta
    w = 2 * math.pi / 240  # 240 passos ~ 2h se STEP_SECONDS=30
    noise = lambda s: random.uniform(-s, s)

    if tag == "qualidade/ph":
        base, amp = 7.05, 0.25
        return max(6.5, min(7.8, base + amp * math.sin(w * i) + noise(0.06)))
    if tag == "decantacao/turbidez":
        base, amp = 0.7, 0.4
        return max(0.1, base + amp * abs(math.sin(w * i / 2)) + noise(0.08))
    if tag == "bombeamento/vazao":
        base, amp = 180, 60
        return max(40, base + amp * math.sin(w * i / 1.5) + noise(8))
    if tag == "qualidade/cloro":
        base, amp = 2.0, 0.35
        return max(0.2, base + amp * math.sin(w * i / 1.8) + noise(0.05))
    if tag == "pressao/linha1":
        base, amp = 3.1, 0.35
        return max(1.2, base + amp * math.sin(w * i) + noise(0.03))
    if tag == "nivel/reservatorio":
        base, amp = 5.0, 1.2
        # tendência lenta (encher/esvaziar)
        trend = 0.4 * math.sin(w * i / 6)
        return max(0.2, base + amp * math.sin(w * i / 2.2) + trend + noise(0.05))
    # fallback
    return 0.0

def main():
    engine = create_engine(DB_URL, pool_pre_ping=True)
    ensure_db(engine)
    tag_to_id = map_tag_to_id(engine)

    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=HOURS_BACK)
    step = timedelta(seconds=STEP_SECONDS)
    n = int((now - start) / step)

    rows = []
    for i in range(n + 1):
        ts = start + i * step
        for tag in TAGS:
            rows.append(
                {
                    "sensor_id": tag_to_id[tag],
                    "ts": ts,
                    "value": float(synth_value(tag, i)),
                }
            )

    insert_sql = text("""
        INSERT INTO eta.measurement (sensor_id, ts, value)
        VALUES (:sensor_id, :ts, :value)
        ON CONFLICT (sensor_id, ts) DO NOTHING;
    """)

    with engine.begin() as conn:
        conn.execute(insert_sql, rows)

    print(f"✅ Seed concluído: {len(rows)} pontos gerados para {len(TAGS)} tags.")

if __name__ == "__main__":
    main()

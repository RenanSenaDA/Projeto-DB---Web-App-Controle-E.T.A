# worker/feeder_loop.py
import os, math, random, time, signal, sys
from datetime import datetime, timezone

from sqlalchemy import create_engine, text

PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = os.getenv("PGPORT", "5432")
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD", "postgres")
PGDATABASE = os.getenv("PGDATABASE", "eta")
DB_URL = os.getenv(
    "DB_URL",
    f"postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}",
)

INTERVAL_SECONDS = int(os.getenv("FEED_INTERVAL", "5"))  # insere a cada 5s

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

def ensure_db(engine):
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS eta;"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS eta.sensor (
                id   SERIAL PRIMARY KEY,
                tag  TEXT NOT NULL UNIQUE,
                unit TEXT,
                meta JSONB
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS eta.measurement (
                id         BIGSERIAL PRIMARY KEY,
                sensor_id  INTEGER NOT NULL REFERENCES eta.sensor(id) ON DELETE CASCADE,
                ts         TIMESTAMPTZ NOT NULL,
                value      DOUBLE PRECISION NOT NULL,
                quality    TEXT,
                meta       JSONB,
                CONSTRAINT uq_sensor_ts UNIQUE(sensor_id, ts)
            );
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_measurement_ts ON eta.measurement(ts);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_measurement_sensor_ts ON eta.measurement(sensor_id, ts DESC);"))
        for tag, unit in UNITS.items():
            conn.execute(
                text("""
                    INSERT INTO eta.sensor(tag, unit)
                    VALUES (:tag, :unit)
                    ON CONFLICT (tag) DO NOTHING;
                """),
                {"tag": tag, "unit": unit},
            )

def map_tag_to_id(engine):
    from sqlalchemy import text
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT id, tag FROM eta.sensor")).fetchall()
    return {tag: sid for (sid, tag) in rows}

def synth_value(tag: str, tick: int) -> float:
    w = 2 * math.pi / 200
    noise = lambda s: random.uniform(-s, s)
    if tag == "qualidade/ph":
        return max(6.5, min(7.8, 7.05 + 0.25 * math.sin(w * tick) + noise(0.06)))
    if tag == "decantacao/turbidez":
        return max(0.1, 0.7 + 0.4 * abs(math.sin(w * tick / 2)) + noise(0.08))
    if tag == "bombeamento/vazao":
        return max(40, 180 + 60 * math.sin(w * tick / 1.5) + noise(8))
    if tag == "qualidade/cloro":
        return max(0.2, 2.0 + 0.35 * math.sin(w * tick / 1.8) + noise(0.05))
    if tag == "pressao/linha1":
        return max(1.2, 3.1 + 0.35 * math.sin(w * tick) + noise(0.03))
    if tag == "nivel/reservatorio":
        trend = 0.4 * math.sin(w * tick / 6)
        return max(0.2, 5.0 + 1.2 * math.sin(w * tick / 2.2) + trend + noise(0.05))
    return 0.0

def main():
    engine = create_engine(DB_URL, pool_pre_ping=True)
    ensure_db(engine)
    tag_to_id = map_tag_to_id(engine)

    insert_sql = text("""
        INSERT INTO eta.measurement (sensor_id, ts, value)
        VALUES (:sensor_id, :ts, :value)
        ON CONFLICT (sensor_id, ts) DO NOTHING;
    """)

    print(f"🚚 Iniciando feeder em {PGHOST}:{PGPORT}/{PGDATABASE} (intervalo={INTERVAL_SECONDS}s). Ctrl+C para parar.")
    tick = 0

    def handle_sigint(signum, frame):
        print("\n🛑 Parando feeder...")
        sys.exit(0)
    signal.signal(signal.SIGINT, handle_sigint)

    while True:
        now = datetime.now(timezone.utc)
        payload = []
        for tag in TAGS:
            payload.append({
                "sensor_id": tag_to_id[tag],
                "ts": now,
                "value": float(synth_value(tag, tick)),
            })
        with engine.begin() as conn:
            conn.execute(insert_sql, payload)
        print(f"[{now.isoformat()}] {len(payload)} medições inseridas.")
        tick += 1
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main()


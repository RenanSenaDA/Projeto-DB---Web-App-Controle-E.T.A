import os
import time
import random
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine, text

TAGS_PADRAO = {
    "qualidade/ph": ("pH", 6.5, 8.5),
    "decantacao/turbidez": ("NTU", 0.1, 5.0),
    "bombeamento/vazao": ("m³/h", 80, 200),
    "qualidade/cloro": ("mg/L", 0.2, 2.0),
    "pressao/linha1": ("bar", 1.5, 3.5),
    "nivel/reservatorio": ("m", 1.0, 5.0),
}

def to_sqlalchemy_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://") and "postgresql+psycopg://" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url

def get_db_url():
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return to_sqlalchemy_url(url)
    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    user = os.getenv("PGUSER", "postgres")
    pwd  = os.getenv("PGPASSWORD", "postgres")
    db   = os.getenv("PGDATABASE", "eta")
    return f"postgresql+psycopg://{user}:{pwd}@{host}:{port}/{db}"

def main():
    interval = int(os.getenv("FEED_INTERVAL", "5"))
    eng = create_engine(get_db_url(), pool_pre_ping=True)

    # garante schema/tabelas e sensores
    with eng.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS eta;"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS eta.sensor(
              id   SERIAL PRIMARY KEY,
              tag  TEXT NOT NULL UNIQUE,
              unit TEXT,
              meta JSONB
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS eta.measurement(
              id        BIGSERIAL PRIMARY KEY,
              sensor_id INT NOT NULL REFERENCES eta.sensor(id) ON DELETE CASCADE,
              ts        TIMESTAMPTZ NOT NULL,
              value     DOUBLE PRECISION NOT NULL,
              quality   TEXT,
              meta      JSONB,
              CONSTRAINT uq_sensor_ts UNIQUE(sensor_id, ts)
            );
        """))
        for tag, (unit, *_rng) in TAGS_PADRAO.items():
            conn.execute(
                text("""INSERT INTO eta.sensor(tag, unit)
                        VALUES (:tag, :unit) ON CONFLICT(tag) DO NOTHING;"""),
                {"tag": tag, "unit": unit},
            )

    with eng.connect() as conn:
        ids = dict(conn.execute(text("SELECT tag, id FROM eta.sensor;")).fetchall())

    print("Feeder iniciado. Intervalo:", interval, "s")
    while True:
        now = datetime.now(timezone.utc)
        rows = []
        for tag, (unit, lo, hi) in TAGS_PADRAO.items():
            base = (lo + hi) / 2
            amp = (hi - lo) / 4
            noise = random.uniform(-amp, amp)
            val = max(min(base + noise, hi), lo)
            rows.append({"sensor_id": ids[tag], "ts": now, "value": float(val), "quality": "good"})
        with eng.begin() as conn:
            conn.execute(
                text("""INSERT INTO eta.measurement(sensor_id, ts, value, quality)
                        VALUES (:sensor_id, :ts, :value, :quality)
                        ON CONFLICT(sensor_id, ts) DO NOTHING;"""),
                rows
            )
        time.sleep(interval)

if __name__ == "__main__":
    main()

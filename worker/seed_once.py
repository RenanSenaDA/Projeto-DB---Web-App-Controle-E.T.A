import os
from datetime import datetime, timedelta, timezone
import random
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

def ensure_schema(engine):
    with engine.begin() as conn:
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
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_measurement_ts ON eta.measurement(ts);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_measurement_sensor_ts ON eta.measurement(sensor_id, ts DESC);"))
        for tag, (unit, *_rng) in TAGS_PADRAO.items():
            conn.execute(
                text("""INSERT INTO eta.sensor(tag, unit)
                        VALUES (:tag, :unit)
                        ON CONFLICT(tag) DO NOTHING;"""),
                {"tag": tag, "unit": unit},
            )

def seed_measurements(engine, minutes=180, step_seconds=30):
    now = datetime.now(timezone.utc)
    start = now - timedelta(minutes=minutes)

    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, tag FROM eta.sensor;")).fetchall()
        id_by_tag = {r.tag: r.id for r in rows}

    inserts = []
    for tag, (unit, lo, hi) in TAGS_PADRAO.items():
        sensor_id = id_by_tag[tag]
        t = start
        val = random.uniform(lo, hi)
        while t <= now:
            val += random.uniform(-0.05*(hi-lo), 0.05*(hi-lo))
            val = max(min(val, hi), lo)
            inserts.append({"sensor_id": sensor_id, "ts": t, "value": float(val), "quality": "good"})
            t += timedelta(seconds=step_seconds)

    with engine.begin() as conn:
        conn.execute(
            text("""INSERT INTO eta.measurement(sensor_id, ts, value, quality)
                    VALUES (:sensor_id, :ts, :value, :quality)
                    ON CONFLICT(sensor_id, ts) DO NOTHING;"""),
            inserts
        )
    print(f"Seed concluído: {len(inserts)} leituras geradas.")

def main():
    db_url = get_db_url()
    print("DB_URL:", db_url.split("@")[-1])  # log sem credencial
    engine = create_engine(db_url, pool_pre_ping=True)
    ensure_schema(engine)
    step = int(os.getenv("FEED_INTERVAL", "5"))
    seed_measurements(engine, minutes=180, step_seconds=step)

if __name__ == "__main__":
    main()

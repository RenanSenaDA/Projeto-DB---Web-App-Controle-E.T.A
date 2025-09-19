CREATE SCHEMA IF NOT EXISTS eta;
SET search_path TO eta, public;

-- 1) Local/Unidades/Dispositivos
CREATE TABLE IF NOT EXISTS site (
  id        SERIAL PRIMARY KEY,
  name      TEXT NOT NULL,
  city      TEXT,
  state     TEXT,
  timezone  TEXT DEFAULT 'UTC',
  meta      JSONB
);

CREATE TABLE IF NOT EXISTS unit (
  id        SERIAL PRIMARY KEY,
  site_id   INT NOT NULL REFERENCES site(id) ON DELETE CASCADE,
  name      TEXT NOT NULL,
  process   TEXT,
  meta      JSONB
);

CREATE TABLE IF NOT EXISTS device (
  id        SERIAL PRIMARY KEY,
  unit_id   INT NOT NULL REFERENCES unit(id) ON DELETE CASCADE,
  vendor    TEXT,
  model     TEXT,
  serial    TEXT UNIQUE,
  protocol  TEXT,
  meta      JSONB
);

-- 2) Sensores/Tags
CREATE TABLE IF NOT EXISTS sensor (
  id          SERIAL PRIMARY KEY,
  device_id   INT NOT NULL REFERENCES device(id) ON DELETE CASCADE,
  tag         TEXT NOT NULL UNIQUE,
  name        TEXT,
  unit        TEXT,
  description TEXT,
  min_valid   DOUBLE PRECISION,
  max_valid   DOUBLE PRECISION,
  decimals    INT DEFAULT 3,
  meta        JSONB
);

-- 3) Gateways
CREATE TABLE IF NOT EXISTS gateway (
  id        SERIAL PRIMARY KEY,
  name      TEXT NOT NULL,
  version   TEXT,
  last_ip   INET,
  meta      JSONB
);

-- 4) Ingestão bruta (staging)
CREATE TABLE IF NOT EXISTS raw_ingest (
  id           BIGSERIAL PRIMARY KEY,
  gateway_id   INT REFERENCES gateway(id) ON DELETE SET NULL,
  received_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  src_topic    TEXT,
  payload      JSONB NOT NULL,
  status       TEXT DEFAULT 'received',  -- received|parsed|failed
  err_msg      TEXT
);
CREATE INDEX IF NOT EXISTS idx_raw_ingest_received_at ON raw_ingest (received_at DESC);
CREATE INDEX IF NOT EXISTS idx_raw_ingest_payload ON raw_ingest USING GIN (payload);

-- 5) Medições curadas
CREATE TABLE IF NOT EXISTS measurement (
  id          BIGSERIAL PRIMARY KEY,
  sensor_id   INT NOT NULL REFERENCES sensor(id) ON DELETE CASCADE,
  ts          TIMESTAMPTZ NOT NULL,
  value       DOUBLE PRECISION NOT NULL,
  quality     BOOLEAN DEFAULT TRUE,
  meta        JSONB,
  UNIQUE(sensor_id, ts)
);
CREATE INDEX IF NOT EXISTS idx_measurement_sensor_ts ON measurement (sensor_id, ts DESC);
CREATE INDEX IF NOT EXISTS idx_measurement_ts ON measurement (ts DESC);

-- 6) Eventos/Alarmes
CREATE TABLE IF NOT EXISTS event (
  id          BIGSERIAL PRIMARY KEY,
  sensor_id   INT NOT NULL REFERENCES sensor(id) ON DELETE CASCADE,
  ts          TIMESTAMPTZ NOT NULL,
  severity    TEXT CHECK (severity IN ('info','warn','crit')) DEFAULT 'info',
  message     TEXT NOT NULL,
  meta        JSONB
);
CREATE INDEX IF NOT EXISTS idx_event_sensor_ts ON event (sensor_id, ts DESC);

-- 7) Calibração
CREATE TABLE IF NOT EXISTS calibration (
  id        SERIAL PRIMARY KEY,
  sensor_id INT NOT NULL REFERENCES sensor(id) ON DELETE CASCADE,
  ts        TIMESTAMPTZ NOT NULL,
  method    TEXT,
  meta      JSONB
);

-- ---------- Timescale opcional ----------
DO $$
BEGIN
  PERFORM 1 FROM pg_extension WHERE extname = 'timescaledb';
  IF FOUND THEN
    -- já existe, ok
  ELSE
    BEGIN
      CREATE EXTENSION IF NOT EXISTS timescaledb;
    EXCEPTION WHEN OTHERS THEN
      -- se não tiver disponível, segue sem Timescale
      RAISE NOTICE 'TimescaleDB não disponível, seguindo sem extensão.';
    END;
  END IF;

  -- tentar criar hypertable se extensão estiver ativa
  IF EXISTS (SELECT 1 FROM pg_extension WHERE extname='timescaledb') THEN
    PERFORM create_hypertable('measurement','ts', if_not_exists => TRUE);
  END IF;
END$$;

-- Views úteis
CREATE OR REPLACE VIEW v_latest_per_sensor AS
SELECT DISTINCT ON (m.sensor_id)
  m.sensor_id, s.tag, s.unit, m.value, m.ts, m.quality
FROM measurement m
JOIN sensor s ON s.id = m.sensor_id
ORDER BY m.sensor_id, m.ts DESC;

CREATE OR REPLACE VIEW v_hourly_avg_24h AS
SELECT s.tag, date_trunc('hour', m.ts) AS hour_bucket,
       AVG(m.value) AS avg_value, MIN(m.value) AS min_value, MAX(m.value) AS max_value
FROM measurement m
JOIN sensor s ON s.id = m.sensor_id
WHERE m.ts >= now() - interval '24 hours'
GROUP BY s.tag, hour_bucket
ORDER BY hour_bucket DESC, s.tag;

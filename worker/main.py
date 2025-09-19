import os, json, time
from datetime import datetime, timezone
from dateutil import parser as dtparser
import paho.mqtt.client as mqtt
import psycopg2
from psycopg2.extras import RealDictCursor

PGHOST = os.getenv("PGHOST", "postgres")
PGPORT = int(os.getenv("PGPORT", "5432"))
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD", "postgres")
PGDATABASE = os.getenv("PGDATABASE", "eta")

MQTT_HOST = os.getenv("MQTT_HOST", "mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "eta/leituras/#")

DEFAULT_SITE = os.getenv("DEFAULT_SITE", "ETA Central")
DEFAULT_UNIT = os.getenv("DEFAULT_UNIT", "Filtração")

def pg_conn():
    return psycopg2.connect(
        host=PGHOST, port=PGPORT, user=PGUSER, password=PGPASSWORD, dbname=PGDATABASE
    )

def ensure_defaults(conn):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT id FROM eta.site WHERE name=%s", (DEFAULT_SITE,))
        row = cur.fetchone()
        if not row:
            cur.execute("INSERT INTO eta.site (name) VALUES (%s) RETURNING id", (DEFAULT_SITE,))
            site_id = cur.fetchone()["id"]
        else:
            site_id = row["id"]

        cur.execute("SELECT id FROM eta.unit WHERE site_id=%s AND name=%s", (site_id, DEFAULT_UNIT))
        row = cur.fetchone()
        if not row:
            cur.execute("""INSERT INTO eta.unit (site_id, name, process)
                           VALUES (%s, %s, %s) RETURNING id""", (site_id, DEFAULT_UNIT, "filtracao"))
            unit_id = cur.fetchone()["id"]
        else:
            unit_id = row["id"]

        cur.execute("SELECT id FROM eta.device WHERE unit_id=%s AND serial=%s", (unit_id, "GW-AUTO"))
        row = cur.fetchone()
        if not row:
            cur.execute("""INSERT INTO eta.device (unit_id, vendor, model, serial, protocol)
                           VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                        (unit_id, "Auto", "Virtual", "GW-AUTO", "mqtt"))
            device_id = cur.fetchone()["id"]
        else:
            device_id = row["id"]

        conn.commit()
        return device_id

def upsert_sensor(conn, device_id, tag, unit=None, desc=None):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM eta.sensor WHERE tag=%s", (tag,))
        r = cur.fetchone()
        if r:
            return r[0]
        cur.execute("""INSERT INTO eta.sensor (device_id, tag, unit, description)
                       VALUES (%s,%s,%s,%s) RETURNING id""",
                    (device_id, tag, unit, desc))
        sensor_id = cur.fetchone()[0]
        conn.commit()
        return sensor_id

def insert_raw(conn, gateway_id, topic, payload_json, status="received", err=None):
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO eta.raw_ingest (gateway_id, src_topic, payload, status, err_msg)
                       VALUES (%s,%s,%s::jsonb,%s,%s) RETURNING id""",
                    (gateway_id, topic, json.dumps(payload_json), status, err))
        rid = cur.fetchone()[0]
        conn.commit()
        return rid

def insert_measurement(conn, sensor_id, ts, value, unit=None, meta=None, quality=True):
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO eta.measurement (sensor_id, ts, value, quality, meta)
                       VALUES (%s,%s,%s,%s,%s)
                       ON CONFLICT (sensor_id, ts) DO NOTHING""",
                    (sensor_id, ts, float(value), quality, json.dumps(meta or {})))
        conn.commit()

def on_message(client, userdata, msg):
    conn = userdata["conn"]
    device_id = userdata["device_id"]

    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except Exception as e:
        try:
            insert_raw(conn, None, msg.topic, {"_raw": msg.payload.decode("utf-8","ignore")}, status="failed", err=str(e))
        except Exception:
            pass
        return

    rid = insert_raw(conn, None, msg.topic, payload, status="received")

    # payload esperado: { "tag": "...", "value": 7.1, "unit": "...", "ts": "2025-09-18T21:27:00Z", "meta": {...} }
    tag = payload.get("tag") or msg.topic.replace("eta/leituras/","")
    unit = payload.get("unit")
    value = payload.get("value")
    ts = payload.get("ts")
    if ts:
        try:
            ts = dtparser.isoparse(ts)
        except Exception:
            ts = datetime.now(timezone.utc)
    else:
        ts = datetime.now(timezone.utc)

    if value is None:
        # marca ingestão como falha
        with conn.cursor() as cur:
            cur.execute("UPDATE eta.raw_ingest SET status='failed', err_msg='missing value' WHERE id=%s", (rid,))
            conn.commit()
        return

    # garante sensor
    sensor_id = upsert_sensor(conn, device_id, tag, unit=unit)

    # insere curado
    insert_measurement(conn, sensor_id, ts, value, unit=unit, meta=payload.get("meta"), quality=True)

    # atualiza status do raw
    with conn.cursor() as cur:
        cur.execute("UPDATE eta.raw_ingest SET status='parsed' WHERE id=%s", (rid,))
        conn.commit()

def main():
    conn = pg_conn()
    device_id = ensure_defaults(conn)

    client = mqtt.Client(userdata={"conn": conn, "device_id": device_id})
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.subscribe(MQTT_TOPIC)
    print(f"[worker] Subscribed to {MQTT_TOPIC} @ {MQTT_HOST}:{MQTT_PORT}")
    client.loop_forever()

if __name__ == "__main__":
    main()

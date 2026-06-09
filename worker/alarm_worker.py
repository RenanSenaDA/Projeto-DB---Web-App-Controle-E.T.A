"""
Worker de alarmes do Aqualink.

Para cada sensor MONITORADO (com algum limite em eta.config_limites), a cada ciclo:
  - detecta SENSOR MUDO (sem leitura há mais de `stale_after_min` min);
  - compara a última leitura contra a FAIXA (limite_min / limite_max) -> alarme
    'low' (abaixo) e/ou 'high' (acima). `limite` legado é tratado como limite_max.
  - registra cada alarme em eta.alarm_event (histórico), usando essa tabela como
    ESTADO/COOLDOWN persistido (sobrevive a restart) com HISTERESE (deadband);
  - re-notifica um alarme em aberto só após o cooldown;
  - RESOLVE automaticamente (status='resolved') quando o valor volta à faixa /
    o sensor volta a reportar.

Notifica por e-mail (Brevo) e WhatsApp, como antes. Estado em memória foi removido.
"""

import os
import re
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg2
from psycopg2.extras import RealDictCursor

from alerts_email import enviar_alerta_para_destinatarios_padrao
from alerts_whatsapp import enviar_alerta_whatsapp

from dotenv import load_dotenv, find_dotenv

# =====================================================================
# Carregamento de .env
# =====================================================================

load_dotenv(find_dotenv())

_base_dir = Path(__file__).resolve().parent
for extra in [
    _base_dir / ".env",
    _base_dir.parent / ".env",
    _base_dir.parent / "eta-stack" / ".env",
    _base_dir.parent / "streamlit" / ".env",
]:
    if extra.exists():
        load_dotenv(extra, override=False)

# =====================================================================
# Config
# =====================================================================

def get_db_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return url
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "postgres")
    pwd = os.getenv("POSTGRES_PASSWORD", "postgres")
    db = os.getenv("POSTGRES_DB", "eta")
    return f"postgresql://{user}:{pwd}@{host}:{port}/{db}"


DB_URL = get_db_url()
CONFIG_SISTEMA_TABLE = (os.getenv("CONFIG_SISTEMA_TABLE", "eta.config_sistema") or "").strip() or "eta.config_sistema"

COOLDOWN_MINUTES = int(os.getenv("ALERT_EMAIL_COOLDOWN_MIN", "10"))
# Histerese (deadband) para evitar "flapping" perto do limite, em % do limite.
DEADBAND_PCT = float(os.getenv("ALARM_DEADBAND_PCT", "2")) / 100.0
# Fallback do stale caso a coluna ainda não exista (migração 0002 pendente).
DEFAULT_STALE_MIN = int(os.getenv("ALARM_STALE_AFTER_MIN", "15"))
POLL_SECONDS = int(os.getenv("ALARM_POLL_SECONDS", "5"))

# =====================================================================
# DB helpers
# =====================================================================

def db_connect():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)


def ensure_config_sistema_row():
    """Garante o registro singleton id=1 (alarmes LIGADOS por padrão)."""
    try:
        conn = db_connect()
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f"SELECT id FROM {CONFIG_SISTEMA_TABLE} WHERE id = 1;")
        if not cur.fetchone():
            cur.execute(
                f"INSERT INTO {CONFIG_SISTEMA_TABLE}(id, alarms_enabled, updated_at) "
                f"VALUES (1, TRUE, now());"
            )
        cur.close()
        conn.close()
    except Exception as e:
        print("[ALARM WORKER] Erro ao garantir config_sistema:", e)


def get_config() -> tuple[bool, int]:
    """Retorna (alarms_enabled, stale_after_min). Fail-safe: alarmes OFF em erro."""
    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(f"SELECT alarms_enabled, stale_after_min FROM {CONFIG_SISTEMA_TABLE} WHERE id = 1;")
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return False, DEFAULT_STALE_MIN
        stale = row.get("stale_after_min")
        return bool(row["alarms_enabled"]), int(stale if stale is not None else DEFAULT_STALE_MIN)
    except Exception as e:
        # Pode cair aqui se a coluna stale_after_min ainda não existir (migração
        # 0002 pendente). Fail-safe OFF; volta a funcionar após `alembic upgrade`.
        print("[ALARM WORKER] get_config falhou (fail-safe OFF):", e)
        return False, DEFAULT_STALE_MIN


def get_last_measurements_with_limits():
    """Última medição por sensor MONITORADO + limites (min/max/legado) + label."""
    query = """
        SELECT
            s.id AS sensor_id,
            COALESCE(m.tag, m.meta->>'tag', s.tag) AS tag,
            m.value,
            m.ts,
            cl.limite,
            cl.limite_min,
            cl.limite_max,
            cl.label
        FROM eta.sensor s
        JOIN LATERAL (
            SELECT m2.tag, m2.value, m2.ts, m2.meta
            FROM eta.measurement m2
            WHERE m2.sensor_id = s.id
            ORDER BY m2.ts DESC
            LIMIT 1
        ) m ON TRUE
        LEFT JOIN eta.config_limites cl
            ON cl.tag = COALESCE(m.tag, m.meta->>'tag', s.tag)
        ORDER BY s.id;
    """
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# =====================================================================
# Nomes amigáveis / formatação
# =====================================================================

PREFIX_LABEL = {"eta": "ETA", "uf": "Ultrafiltração", "utf": "Ultrafiltração", "fc": "Carvão", "carvao": "Carvão"}


def fallback_pretty_name(tag: str) -> str:
    t = (tag or "").strip()
    parts = [p.strip() for p in t.split("/") if p.strip()]
    if len(parts) < 2:
        return t
    prefix = parts[0].lower()
    area = parts[1].title()
    nome = " / ".join(parts[2:]) if len(parts) > 2 else ""
    prefix_label = PREFIX_LABEL.get(prefix, parts[0].upper())
    nome = nome.replace("M3/h", "m³/h").replace("M3/dia", "m³/dia").replace("M3/d", "m³/d")
    nome = re.sub(r"\s+", " ", nome).strip()
    return f"{prefix_label} • {area} • {nome}" if nome else f"{prefix_label} • {area}"


def resolve_display_name(tag: str, label) -> str:
    if label and str(label).strip():
        return str(label).strip()
    return fallback_pretty_name(tag)


def format_ts_local(ts) -> str:
    tz = ZoneInfo(os.getenv("TZ", "America/Fortaleza"))
    if ts is None:
        return datetime.now(tz).strftime("%d/%m/%Y %H:%M")
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(tz).strftime("%d/%m/%Y %H:%M")

# =====================================================================
# Mensagens e notificação
# =====================================================================

def build_message(kind: str, value, threshold, stale_min: int, ts_fmt: str) -> str:
    if kind == "high":
        return f"Condição: valor ACIMA do limite ({value:.2f} > {threshold:.2f})."
    if kind == "low":
        return f"Condição: valor ABAIXO do limite ({value:.2f} < {threshold:.2f})."
    if kind == "stale":
        return f"Condição: SENSOR SEM LEITURA há mais de {stale_min} min (última: {ts_fmt})."
    return "Condição de alarme."


def notify(kind: str, tag: str, label, value, threshold, stale_min: int, ts):
    nome = resolve_display_name(tag, label)
    ts_fmt = format_ts_local(ts)
    msg = build_message(kind, value, threshold, stale_min, ts_fmt)
    extra = f"TAG: {tag}\n{msg}"
    print(f"[ALERTA] {kind.upper()} | {nome} (TAG={tag}) | {msg}")

    valor_kpi = f"{value:.2f}" if value is not None else "—"
    try:
        enviar_alerta_para_destinatarios_padrao(equipamento=nome, valor_kpi=valor_kpi, mensagem_extra=extra)
    except Exception as e:
        print("[ERRO EMAIL]", e)
    try:
        enviar_alerta_whatsapp(
            parametro=nome,
            valor_atual=value if value is not None else 0,
            limite=threshold if threshold is not None else 0,
            timestamp_str=ts_fmt,
        )
    except Exception as e:
        print("[ERRO WPP]", e)

# =====================================================================
# Estado / histerese (via eta.alarm_event)
# =====================================================================

def _in_hysteresis(kind: str, value, threshold) -> bool:
    """Mantém o alarme aberto na 'banda morta' (evita flapping na resolução)."""
    if value is None or threshold is None:
        return False
    if kind == "high":
        return value > threshold * (1.0 - DEADBAND_PCT)
    if kind == "low":
        return value < threshold * (1.0 + DEADBAND_PCT)
    return False  # 'stale' não usa deadband


def handle_alarm(cur, now, sensor_id, tag, label, kind, raw_active, value, threshold, stale_min, ts):
    """Abre / re-notifica / resolve um alarme (tag, kind) usando eta.alarm_event."""
    cur.execute(
        "SELECT id, last_notified_at FROM eta.alarm_event "
        "WHERE tag = %s AND kind = %s AND status = 'open' ORDER BY opened_at DESC LIMIT 1;",
        (tag, kind),
    )
    ev = cur.fetchone()

    if ev is None:
        if raw_active:
            msg = build_message(kind, value, threshold, stale_min, format_ts_local(ts))
            cur.execute(
                "INSERT INTO eta.alarm_event "
                "(sensor_id, tag, kind, severity, status, value, threshold, message, opened_at, last_notified_at) "
                "VALUES (%s, %s, %s, 'warn', 'open', %s, %s, %s, now(), now());",
                (sensor_id, tag, kind, value, threshold, msg),
            )
            notify(kind, tag, label, value, threshold, stale_min, ts)
        return

    # Já existe um alarme ABERTO para (tag, kind).
    if raw_active or _in_hysteresis(kind, value, threshold):
        last = ev.get("last_notified_at")
        if last is None or (now - last) >= timedelta(minutes=COOLDOWN_MINUTES):
            cur.execute("UPDATE eta.alarm_event SET last_notified_at = now() WHERE id = %s;", (ev["id"],))
            notify(kind, tag, label, value, threshold, stale_min, ts)
    else:
        cur.execute(
            "UPDATE eta.alarm_event SET status = 'resolved', resolved_at = now() WHERE id = %s;",
            (ev["id"],),
        )
        print(f"[ALARM] RESOLVIDO: tag={tag} kind={kind}")

# =====================================================================
# Ciclo principal
# =====================================================================

def check_alerts():
    enabled, stale_min = get_config()
    if not enabled:
        print("[ALARM WORKER] Alarmes desativados.")
        return

    try:
        rows = get_last_measurements_with_limits()
    except Exception as e:
        print("[ALARM WORKER] Erro ao buscar medições:", e)
        return

    if not rows:
        print("[ALARM WORKER] Nenhuma leitura encontrada.")
        return

    now = datetime.now(timezone.utc)
    conn = db_connect()
    conn.autocommit = True
    cur = conn.cursor()
    try:
        for r in rows:
            sensor_id = r.get("sensor_id")
            tag = (r.get("tag") or "").strip()
            ts = r.get("ts")
            raw_v = r.get("value")
            limite = r.get("limite")
            limite_min = r.get("limite_min")
            limite_max = r.get("limite_max")
            label = r.get("label")

            # limite_max efetivo: usa limite_max; senão o `limite` legado (era superior)
            max_thr = limite_max if limite_max is not None else limite
            min_thr = limite_min

            # Sensor NÃO monitorado (sem nenhum limite) -> ignora.
            if max_thr is None and min_thr is None:
                continue

            try:
                v = float(raw_v) if raw_v is not None else None
            except Exception:
                v = None

            ts_utc = ts
            if ts_utc is not None and ts_utc.tzinfo is None:
                ts_utc = ts_utc.replace(tzinfo=timezone.utc)

            stale_active = ts_utc is None or (now - ts_utc) > timedelta(minutes=stale_min)

            # SENSOR MUDO
            handle_alarm(cur, now, sensor_id, tag, label, "stale", stale_active, v, None, stale_min, ts_utc)

            if stale_active:
                # Dado velho: não avalia high/low (mantém eventuais abertos como estão).
                continue

            # ACIMA / ABAIXO da faixa
            if v is not None and max_thr is not None:
                try:
                    handle_alarm(cur, now, sensor_id, tag, label, "high", v > float(max_thr), v, float(max_thr), stale_min, ts_utc)
                except Exception as e:
                    print(f"[ALARM] erro high tag={tag}:", e)
            if v is not None and min_thr is not None:
                try:
                    handle_alarm(cur, now, sensor_id, tag, label, "low", v < float(min_thr), v, float(min_thr), stale_min, ts_utc)
                except Exception as e:
                    print(f"[ALARM] erro low tag={tag}:", e)
    finally:
        cur.close()
        conn.close()


def main_loop():
    print(f"[ALARM WORKER] Iniciado. cooldown={COOLDOWN_MINUTES}min deadband={DEADBAND_PCT*100:.0f}% poll={POLL_SECONDS}s")
    ensure_config_sistema_row()
    while True:
        try:
            check_alerts()
        except Exception as e:
            print("[ALARM WORKER] Erro inesperado:", e)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main_loop()

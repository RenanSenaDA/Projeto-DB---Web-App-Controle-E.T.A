import os
import time
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg2
from psycopg2.extras import RealDictCursor

from alerts_email import enviar_alerta_para_destinatarios_padrao
from alerts_whatsapp import enviar_alerta_whatsapp

from dotenv import load_dotenv, find_dotenv

# =====================================================================
# Carregamento de .env (compatível com seu ambiente)
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
# DB / CONFIG
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

# cooldown por TAG EXATA
ultimo_disparo: dict[str, datetime] = {}

# =====================================================================
# Utilitários
# =====================================================================

def db_connect():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)


def ensure_config_sistema_row():
    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(f"SELECT id FROM {CONFIG_SISTEMA_TABLE} WHERE id = 1;")
        if not cur.fetchone():
            cur.execute(
                f"""
                INSERT INTO {CONFIG_SISTEMA_TABLE}(id, alarms_enabled, updated_at)
                VALUES (1, FALSE, now());
                """
            )
            conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("[ALARM WORKER] Erro ao garantir config_sistema:", e)


def is_alarms_enabled() -> bool:
    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(f"SELECT alarms_enabled FROM {CONFIG_SISTEMA_TABLE} WHERE id = 1;")
        row = cur.fetchone()
        cur.close()
        conn.close()

        enabled = bool(row["alarms_enabled"]) if row else False
        print(f"[ALARM WORKER] alarms_enabled (DB) = {enabled}")
        return enabled
    except Exception as e:
        print("[ALARM WORKER] Falha ao ler alarms_enabled. Fail-safe OFF.", e)
        return False


def tag_key(tag: str | None) -> str:
    return (tag or "").strip().lower()


def should_trigger(key: str) -> bool:
    now = datetime.now(timezone.utc)
    last = ultimo_disparo.get(key)
    if last is None:
        return True
    return (now - last) >= timedelta(minutes=COOLDOWN_MINUTES)


def register_trigger(key: str):
    ultimo_disparo[key] = datetime.now(timezone.utc)


def format_ts_local(ts):
    tz_name = os.getenv("TZ", "America/Fortaleza")
    tz = ZoneInfo(tz_name)

    if ts is None:
        return datetime.now(tz).strftime("%d/%m/%Y %H:%M")

    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    return ts.astimezone(tz).strftime("%d/%m/%Y %H:%M")


PREFIX_LABEL = {
    "eta": "ETA",
    "uf": "Ultrafiltração",
    "utf": "Ultrafiltração",
    "fc": "Carvão",
    "carvao": "Carvão",
}

def fallback_pretty_name(tag: str) -> str:
    """
    Fallback caso não exista label no DB.
    """
    t = (tag or "").strip()
    parts = [p.strip() for p in t.split("/") if p.strip()]
    if len(parts) < 2:
        return t

    prefix = parts[0].lower()
    area = parts[1].title()
    nome = " / ".join(parts[2:]) if len(parts) > 2 else ""

    prefix_label = PREFIX_LABEL.get(prefix, parts[0].upper())

    nome = (
        nome.replace("M3/h", "m³/h")
            .replace("M3/dia", "m³/dia")
            .replace("M3/d", "m³/d")
    )
    nome = re.sub(r"\s+", " ", nome).strip()

    if nome:
        return f"{prefix_label} • {area} • {nome}"
    return f"{prefix_label} • {area}"


def resolve_display_name(tag: str, label: str | None) -> str:
    """
    Nome amigável:
      - Se label existir e não estiver vazio -> usa label
      - Senão -> fallback bonito derivado da tag
    """
    if label and str(label).strip():
        return str(label).strip()
    return fallback_pretty_name(tag)


def montar_mensagem_extra(tag_original: str, valor_atual: float, limite: float) -> str:
    return (
        f"TAG: {tag_original}\n"
        f"Condição: valor acima do limite configurado ({valor_atual:.2f} > {limite:.2f})."
    )


# =====================================================================
# Query principal: última medição + limite + label
# =====================================================================

def get_last_measurements_with_limits_and_label():
    query = """
        SELECT
            s.id AS sensor_id,
            COALESCE(m.tag, m.meta->>'tag', s.tag) AS tag,
            m.value,
            m.ts,
            cl.limite,
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
# Loop
# =====================================================================

def check_alerts():
    print("\n[ALARM WORKER] Verificando sensores...")

    if not is_alarms_enabled():
        print("[ALARM WORKER] Alarmes desativados.")
        return

    try:
        rows = get_last_measurements_with_limits_and_label()
    except Exception as e:
        print("[ALARM WORKER] Erro ao buscar medições:", e)
        return

    if not rows:
        print("[ALARM WORKER] Nenhuma leitura encontrada.")
        return

    for r in rows:
        sensor_id = r.get("sensor_id")
        tag = (r.get("tag") or "").strip()
        value = r.get("value")
        ts = r.get("ts")
        limite = r.get("limite")
        label = r.get("label")

        # Sem limite cadastrado => sem alarme configurado para essa KPI
        if limite is None:
            print(f"[DEBUG] sensor_id={sensor_id}, tag={tag} -> sem limite em config_limites (ignorado).")
            continue

        if value is None:
            print(f"[DEBUG] sensor_id={sensor_id}, tag={tag} -> value None (ignorado).")
            continue

        try:
            v = float(value)
            lim = float(limite)
        except Exception:
            print(f"[DEBUG] sensor_id={sensor_id}, tag={tag} -> value/limite inválido (ignorado).")
            continue

        key = tag_key(tag)
        condicao = v > lim
        cooldown_ok = should_trigger(key)

        print(
            f"[DEBUG] sensor_id={sensor_id}, tag={tag}, label={label}, "
            f"value={v}, limite={lim}, condicao={condicao}, cooldown_ok={cooldown_ok}"
        )

        if condicao and cooldown_ok:
            ts_fmt = format_ts_local(ts)

            nome_bonito = resolve_display_name(tag, label)
            msg_extra = montar_mensagem_extra(tag_original=tag, valor_atual=v, limite=lim)

            print(f"[ALERTA] Disparando: {nome_bonito} | TAG='{tag}' ({v} > {lim})")

            # Email (mostra nome bonito, mas inclui TAG no texto)
            try:
                enviar_alerta_para_destinatarios_padrao(
                    equipamento=nome_bonito,
                    valor_kpi=f"{v:.2f}",
                    mensagem_extra=msg_extra,
                )
            except Exception as e:
                print("[ERRO EMAIL]", e)

            # WhatsApp
            try:
                enviar_alerta_whatsapp(
                    parametro=nome_bonito,
                    valor_atual=v,
                    limite=lim,
                    timestamp_str=ts_fmt,
                )
            except Exception as e:
                print("[ERRO WPP]", e)

            register_trigger(key)


def main_loop():
    print(f"[ALARM WORKER] Worker iniciado. Tabela: {CONFIG_SISTEMA_TABLE}")
    ensure_config_sistema_row()
    while True:
        try:
            check_alerts()
        except Exception as e:
            print("[ALARM WORKER] Erro inesperado:", e)
        time.sleep(5)


if __name__ == "__main__":
    main_loop()

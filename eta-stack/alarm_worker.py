import os
import time
from datetime import datetime, timezone, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor

from alerts_email import enviar_alerta_para_destinatarios_padrao
from alerts_whatsapp import enviar_alerta_whatsapp

# =====================================================================
# CONFIG GERAL
# =====================================================================

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não definido nas variáveis de ambiente.")

COOLDOWN_MINUTES = int(os.getenv("ALERT_EMAIL_COOLDOWN_MIN", "10"))

# cooldown por TAG EXATA (cada KPI é independente)
ultimo_disparo: dict[str, datetime] = {}


# =====================================================================
# FUNÇÕES AUXILIARES
# =====================================================================

def db_connect():
    return psycopg2.connect(DATABASE_URL)


def tag_key(tag: str | None) -> str:
    """Normaliza somente para uso interno de cooldown (não para lookup de limite)."""
    return (tag or "").strip().lower()


def should_trigger(key: str) -> bool:
    agora = datetime.now(timezone.utc)
    last = ultimo_disparo.get(key)
    if last is None:
        return True
    return (agora - last) >= timedelta(minutes=COOLDOWN_MINUTES)


def register_trigger(key: str):
    ultimo_disparo[key] = datetime.now(timezone.utc)


def load_alarms_enabled(conn) -> bool:
    """
    Lê alarms_enabled da tabela eta.config_sistema (id=1).
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT alarms_enabled FROM eta.config_sistema WHERE id = 1;")
        row = cur.fetchone()
    return bool(row.get("alarms_enabled", True)) if row else True


def get_last_measurements_with_limits(conn):
    """
    Busca a ÚLTIMA leitura de cada sensor e tenta casar com o limite
    cadastrado em eta.config_limites pela TAG EXATA (PK tag).

    Se não existir limite para a tag (limite = NULL), significa:
    "alarme não configurado" -> worker ignora.
    """
    query = """
        SELECT
            s.id AS sensor_id,
            COALESCE(m.tag, m.meta->>'tag', s.tag) AS tag,
            m.value,
            m.ts,
            cl.limite
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
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        return cur.fetchall()


# =====================================================================
# LOOP PRINCIPAL DE CHECAGEM
# =====================================================================

def check_alerts():
    print("[ALARM WORKER] Verificando sensores...")

    try:
        conn = db_connect()
    except Exception as e:
        print("[ALARM WORKER] ERRO abrindo conexão com banco:", e)
        return

    try:
        alarms_enabled = load_alarms_enabled(conn)
        print("[ALARM WORKER] alarms_enabled (DB) =", alarms_enabled)

        if not alarms_enabled:
            print("[ALARM WORKER] Alarmes DESATIVADOS em eta.config_sistema. Não dispara nada.")
            return

        rows = get_last_measurements_with_limits(conn)
        if not rows:
            print("[ALARM WORKER] Nenhuma leitura encontrada.")
            return

        for r in rows:
            sensor_id = r.get("sensor_id")
            tag_original = r.get("tag") or ""
            value = r.get("value")
            ts = r.get("ts")
            limite = r.get("limite")  # vem de eta.config_limites

            # Sem limite cadastrado = sem alarme configurado para esta KPI
            if limite is None:
                print(f"[DEBUG] sensor_id={sensor_id}, tag={tag_original} -> sem limite em config_limites (ignorado).")
                continue

            if value is None:
                print(f"[DEBUG] sensor_id={sensor_id}, tag={tag_original} -> value None (ignorado).")
                continue

            try:
                valor_float = float(value)
                limite_float = float(limite)
            except Exception:
                print(f"[DEBUG] sensor_id={sensor_id}, tag={tag_original} -> value/limite inválido (ignorado).")
                continue

            key = tag_key(tag_original)
            condicao = valor_float > limite_float
            cooldown_ok = should_trigger(key)

            print(
                f"[DEBUG] sensor_id={sensor_id}, tag={tag_original}, "
                f"value={valor_float}, limite={limite_float}, "
                f"condicao={condicao}, cooldown_ok={cooldown_ok}"
            )

            if condicao:
                if cooldown_ok:
                    nome = tag_original  # NOME EXATO da KPI (como aparece no frontend)

                    print(
                        f"[ALERTA] Disparando: tag='{nome}' "
                        f"(valor={valor_float}, limite={limite_float}, ts={ts})"
                    )

                    # E-MAIL
                    try:
                        enviar_alerta_para_destinatarios_padrao(
                            equipamento=nome,
                            valor_kpi=valor_float,
                            mensagem_extra=(
                                f"TAG '{nome}' acima do limite configurado "
                                f"({valor_float} > {limite_float})."
                            ),
                        )
                        print(f"[ALERTA-EMAIL] Envio disparado para '{nome}'.")
                    except Exception as e:
                        print("[ERRO EMAIL] ao enviar alerta:", e)

                    # WHATSAPP
                    try:
                        enviar_alerta_whatsapp(
                            parametro=nome,
                            valor_atual=valor_float,
                            limite=limite_float,
                            timestamp_str=ts.strftime("%d/%m/%Y %H:%M") if ts else datetime.now().strftime("%d/%m/%Y %H:%M"),
                        )
                        print(f"[ALERTA-WPP] Envio disparado para '{nome}'.")
                    except Exception as e:
                        print("[ERRO WPP] ao enviar alerta WPP:", e)

                    register_trigger(key)
                else:
                    print(f"[DEBUG] tag='{tag_original}' acima do limite mas em cooldown.")
            else:
                print(f"[DEBUG] tag='{tag_original}' dentro do limite.")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def main_loop():
    print("[ALARM WORKER] Motor de alarmes iniciado. Rodando em loop 24/7...")
    while True:
        try:
            check_alerts()
        except Exception as e:
            print("[ALARM WORKER] Erro inesperado no loop principal:", e)
        time.sleep(5)


if __name__ == "__main__":
    main_loop()

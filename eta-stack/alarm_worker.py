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

# chaves de limite iguais às do Streamlit
DEFAULT_LIMITS_BY_TAG = {
    "qualidade/ph": 8.0,
    "decantacao/turbidez": 8.0,
    "bombeamento/vazao": 300.0,
    "qualidade/cloro": 400.0,
    "pressao/linha1": 5.0,
    "nivel/reservatorio": 22000.0,
}

# mapeia o "tipo" (derivado da tag do plc) para a chave de limite
TIPO_PARA_CHAVE = {
    "ph": "qualidade/ph",
    "turbidez": "decantacao/turbidez",
    "vazao": "bombeamento/vazao",
    "cloro": "qualidade/cloro",
    "pressao": "pressao/linha1",
    "nivel": "nivel/reservatorio",
}

# cooldown por TAG NORMALIZADA (ph, vazao, nivel, etc.)
ultimo_disparo: dict[str, datetime] = {}

NOMES_AMIGAVEIS = {
    "ph": "pH",
    "pressao": "Pressão",
    "turbidez": "Turbidez",
    "cloro": "Cloro",
    "vazao": "Vazão",
    "nivel": "Nível do Reservatório",
}


# =====================================================================
# FUNÇÕES AUXILIARES
# =====================================================================

def db_connect():
    return psycopg2.connect(DATABASE_URL)


def normalizar_tipo(tag_original: str | None) -> str | None:
    if not tag_original:
        return None
    tl = tag_original.lower().strip()
    if "ph" in tl:
        return "ph"
    if "pressao" in tl or "pressão" in tl:
        return "pressao"
    if "turbidez" in tl:
        return "turbidez"
    if "cloro" in tl:
        return "cloro"
    if "vazao" in tl or "vazão" in tl:
        return "vazao"
    if "nivel" in tl or "nível" in tl:
        return "nivel"
    return None


def should_trigger(tag_norm: str) -> bool:
    agora = datetime.now(timezone.utc)
    last = ultimo_disparo.get(tag_norm)
    if last is None:
        return True
    return (agora - last) >= timedelta(minutes=COOLDOWN_MINUTES)


def register_trigger(tag_norm: str):
    ultimo_disparo[tag_norm] = datetime.now(timezone.utc)


def load_config_and_limits(conn) -> tuple[bool, dict]:
    """
    Lê alarms_enabled e limites_json da tabela config_sistema.
    Retorna (alarms_enabled, limits_by_tag_lower).
    """
    limits = {k.lower(): v for k, v in DEFAULT_LIMITS_BY_TAG.items()}
    alarms_enabled = True

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT alarms_enabled, limites_json "
            "FROM config_sistema WHERE id = 1;"
        )
        row = cur.fetchone()

    if row:
        alarms_enabled = bool(row.get("alarms_enabled", True))
        lj = row.get("limites_json")
        if isinstance(lj, dict):
            for k, v in lj.items():
                try:
                    limits[str(k).lower()] = float(v)
                except (TypeError, ValueError):
                    continue

    return alarms_enabled, limits


def get_last_measurements(conn):
    """
    Busca a ÚLTIMA leitura de cada sensor na eta.measurement.
    """
    query = """
        SELECT
            s.id AS sensor_id,
            COALESCE(m.tag, m.meta->>'tag', s.tag) AS tag,
            m.value,
            m.ts
        FROM eta.sensor s
        JOIN LATERAL (
            SELECT m2.tag, m2.value, m2.ts
            FROM eta.measurement m2
            WHERE m2.sensor_id = s.id
            ORDER BY m2.ts DESC
            LIMIT 1
        ) m ON TRUE
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
        alarms_enabled, limits_by_tag = load_config_and_limits(conn)
        print("[ALARM WORKER] Limits by TAG:", limits_by_tag)

        if not alarms_enabled:
            print("[ALARM WORKER] Alarmes DESATIVADOS em config_sistema. Não dispara nada.")
            return

        rows = get_last_measurements(conn)
        if not rows:
            print("[ALARM WORKER] Nenhuma leitura encontrada.")
            return

        for r in rows:
            sensor_id = r.get("sensor_id")
            tag_original = r.get("tag") or ""
            value = r.get("value")
            ts = r.get("ts")

            tipo = normalizar_tipo(tag_original)
            if not tipo:
                print(f"[DEBUG] sensor_id={sensor_id}, tag_original={tag_original}: tipo não reconhecido.")
                continue

            tag_norm = tipo  # cooldown por tipo (ph, vazao, nivel...)

            print(
                f"[DEBUG] sensor_id={sensor_id}, tag_original={tag_original}, "
                f"tipo={tipo}, value={value}, ts={ts}"
            )

            if value is None:
                print(f"[DEBUG] Valor None para tipo='{tipo}'. Ignorando.")
                continue

            valor_float = float(value)

            # pega a chave de limite associada ao tipo
            chave_limite = TIPO_PARA_CHAVE.get(tipo)
            if not chave_limite:
                print(f"[DEBUG] Tipo '{tipo}' sem chave de limite configurada. Ignorando.")
                continue

            limite = limits_by_tag.get(chave_limite.lower())
            if limite is None:
                print(
                    f"[DEBUG] Nenhum limite encontrado para chave_limite='{chave_limite}' "
                    f"(tipo='{tipo}'). Ignorando."
                )
                continue

            limite = float(limite)

            print(
                f"[DEBUG] tipo='{tipo}', chave_limite='{chave_limite}', "
                f"valor_atual={valor_float}, limite={limite}"
            )

            if valor_float > limite:
                if should_trigger(tag_norm):
                    nome = NOMES_AMIGAVEIS.get(tipo, tag_original)

                    print(
                        f"[ALERTA] Disparando ALARME de '{nome}' "
                        f"(tipo={tipo}, valor={valor_float}, limite={limite}, ts={ts})"
                    )

                    # E-MAIL
                    try:
                        enviar_alerta_para_destinatarios_padrao(
                            equipamento=nome,
                            valor_kpi=valor_float,
                            mensagem_extra=(
                                f"Equipamento {nome} acima do limite configurado "
                                f"({valor_float} > {limite}). Tag original: {tag_original}"
                            ),
                        )
                        print(f"[ALERTA-EMAIL] Envio disparado para '{nome}'.")
                    except Exception as e:
                        print("[ERRO EMAIL] ao enviar alerta:", e)

                    # WHATSAPP
                    try:
                        enviar_alerta_whatsapp(
                            equipamento=nome,
                            valor_kpi=valor_float,
                            limite=limite,
                        )
                        print(f"[ALERTA-WPP] Envio disparado para '{nome}'.")
                    except Exception as e:
                        print("[ERRO WPP] ao enviar alerta WPP:", e)

                    register_trigger(tag_norm)
                else:
                    print(
                        f"[DEBUG] tipo='{tipo}' acima do limite mas em cooldown "
                        f"(valor={valor_float}, limite={limite})."
                    )
            else:
                print(
                    f"[DEBUG] tipo='{tipo}' dentro do limite "
                    f"(valor={valor_float}, limite={limite})."
                )
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

import os
import time
from datetime import datetime, timezone, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor

from alerts_email import enviar_alerta_para_destinatarios_padrao
from alerts_whatsapp import enviar_alerta_whatsapp

# ==========================================================
# CONFIGURAÇÕES GERAIS
# ==========================================================

DATABASE_URL = os.getenv("DATABASE_URL")
COOLDOWN_MINUTES = 10  # 10 min entre disparos por tipo (ph, vazao, nivel...)
ULTIMO_DISPARO = {}    # ex: { "ph": datetime(...), "nivel": datetime(...) }


def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


# ----------------------------------------------------------
# Leitura do status global (liga/desliga) e limites do banco
# ----------------------------------------------------------

def get_alarms_enabled(conn) -> bool:
    """
    Lê config_sistema. Se não existir, considera True.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT alarms_enabled
        FROM config_sistema
        WHERE id = 1;
        """
    )
    row = cur.fetchone()
    cur.close()
    if not row:
        return True
    return bool(row["alarms_enabled"])


def get_limites_alerta(conn) -> dict:
    """
    Lê tabela de limites (eta.config_limites).
    Se não existir ou estiver vazia, usa defaults.
    """
    limites = {
        "qualidade/ph": 7.0,
        "decantacao/turbidez": 10.0,
        "bombeamento/vazao": 300.0,
        "qualidade/cloro": 900.0,
        "pressao/linha1": 5.0,
        "nivel/reservatorio": 22000.0,
    }

    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT tag, limite
            FROM eta.config_limites;
            """
        )
        for row in cur.fetchall():
            tag = row["tag"]
            limite = float(row["limite"])
            limites[tag] = limite
        cur.close()
    except Exception as e:
        print("[ALARM WORKER] Aviso: não consegui ler eta.config_limites:", e)

    return limites


# ----------------------------------------------------------
# Cooldown
# ----------------------------------------------------------

def should_trigger(tipo: str) -> bool:
    agora = datetime.now(timezone.utc)
    last = ULTIMO_DISPARO.get(tipo)
    if last is None:
        return True
    return (agora - last) >= timedelta(minutes=COOLDOWN_MINUTES)


def register_trigger(tipo: str):
    ULTIMO_DISPARO[tipo] = datetime.now(timezone.utc)


# ----------------------------------------------------------
# Normalização de tags
# ----------------------------------------------------------

def detectar_tipo_sensor(tag: str) -> str | None:
    """
    Recebe a tag bruta (ex.: 'ph', 'pressao', 'nivel', 'bombeamento/vazao')
    e devolve um tipo lógico: 'ph', 'pressao', 'turbidez', 'cloro',
    'vazao', 'nivel' ou None.
    """
    if not tag:
        return None

    t = tag.lower().strip()

    if "ph" in t:
        return "ph"
    if "press" in t:
        return "pressao"
    if "turbid" in t:
        return "turbidez"
    if "cloro" in t:
        return "cloro"
    if "vazao" in t:
        return "vazao"
    if "nivel" in t or "reservatorio" in t:
        return "nivel"

    return None


# ----------------------------------------------------------
# Leitura das últimas medições
# ----------------------------------------------------------

def get_ultimas_medidas(conn):
    """
    Lê últimas medições da tabela eta.measurement.
    Pegamos um recorte recente e deixamos ordenar por ts desc.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            sensor_id,
            COALESCE(tag, meta->>'tag') AS tag,
            value,
            ts
        FROM eta.measurement
        WHERE ts >= (NOW() - INTERVAL '15 minutes')
        ORDER BY ts DESC;
        """
    )
    rows = cur.fetchall()
    cur.close()
    return rows


# ==========================================================
# LOOP PRINCIPAL DE ALERTAS
# ==========================================================

def check_alerts():
    print("[ALARM WORKER] Verificando sensores...")

    conn = get_conn()

    try:
        # 1) Checa se alarmes estão ligados
        if not get_alarms_enabled(conn):
            print("[ALARM WORKER] Alarmes desativados em config_sistema. Não enviarei notificações.")
            conn.close()
            return

        # 2) Lê limites do banco
        limites = get_limites_alerta(conn)
        print("[ALARM WORKER] Limites em uso:", limites)

        # 3) Busca últimas medidas
        rows = get_ultimas_medidas(conn)
        if not rows:
            print("[ALARM WORKER] Nenhuma medida recente encontrada.")
            conn.close()
            return

        for row in rows:
            sensor_id = row["sensor_id"]
            tag_original = row["tag"]
            value = row["value"]
            ts = row["ts"]

            tag_tipo = detectar_tipo_sensor(tag_original)

            print(
                f"[DEBUG] sensor_id={sensor_id}, "
                f"tag_original={tag_original}, tag_tipo={tag_tipo}, "
                f"value={value}, ts={ts}"
            )

            if tag_tipo is None or value is None:
                continue

            # ----------------------------------------------
            # Define limites específicos por tipo
            # ----------------------------------------------
            limite_ph = limites.get("qualidade/ph", 7.0)
            limite_turbidez = limites.get("decantacao/turbidez", 10.0)
            limite_vazao = limites.get("bombeamento/vazao", 300.0)
            limite_cloro = limites.get("qualidade/cloro", 900.0)
            limite_pressao = limites.get("pressao/linha1", 5.0)
            limite_nivel = limites.get("nivel/reservatorio", 22000.0)

            # ----------------------------------------------
            # Regras de disparo
            # ----------------------------------------------

            # pH ALTO
            if tag_tipo == "ph" and value > limite_ph and should_trigger("ph"):
                msg_console = (
                    f"⚠️ ALARME de pH ALTO! valor={value}, "
                    f"limite={limite_ph}, ts={ts}, tag={tag_original}"
                )
                print("[ALERTA] Disparando:", msg_console)

                try:
                    enviar_alerta_para_destinatarios_padrao(
                        equipamento="pH",
                        valor_kpi=value,
                        limite=limite_ph,
                    )
                except Exception as e:
                    print("[ERRO EMAIL] ao enviar alerta de pH:", e)

                try:
                    enviar_alerta_whatsapp(
                        equipamento="pH",
                        valor_kpi=value,
                        limite=limite_ph,
                    )
                except Exception as e:
                    print("[ERRO WPP] ao enviar alerta de pH:", e)

                register_trigger("ph")

            # TURBIDEZ ALTA
            if tag_tipo == "turbidez" and value > limite_turbidez and should_trigger("turbidez"):
                msg_console = (
                    f"⚠️ ALARME de TURBIDEZ ALTA! valor={value}, "
                    f"limite={limite_turbidez}, ts={ts}, tag={tag_original}"
                )
                print("[ALERTA] Disparando:", msg_console)

                try:
                    enviar_alerta_para_destinatarios_padrao(
                        equipamento="Turbidez",
                        valor_kpi=value,
                        limite=limite_turbidez,
                    )
                except Exception as e:
                    print("[ERRO EMAIL] ao enviar alerta de turbidez:", e)

                try:
                    enviar_alerta_whatsapp(
                        equipamento="Turbidez",
                        valor_kpi=value,
                        limite=limite_turbidez,
                    )
                except Exception as e:
                    print("[ERRO WPP] ao enviar alerta de turbidez:", e)

                register_trigger("turbidez")

            # VAZÃO ALTA
            if tag_tipo == "vazao" and value > limite_vazao and should_trigger("vazao"):
                msg_console = (
                    f"⚠️ ALARME de VAZÃO ALTA! valor={value}, "
                    f"limite={limite_vazao}, ts={ts}, tag={tag_original}"
                )
                print("[ALERTA] Disparando:", msg_console)

                try:
                    enviar_alerta_para_destinatarios_padrao(
                        equipamento="Vazão",
                        valor_kpi=value,
                        limite=limite_vazao,
                    )
                except Exception as e:
                    print("[ERRO EMAIL] ao enviar alerta de vazão:", e)

                try:
                    enviar_alerta_whatsapp(
                        equipamento="Vazão",
                        valor_kpi=value,
                        limite=limite_vazao,
                    )
                except Exception as e:
                    print("[ERRO WPP] ao enviar alerta de vazão:", e)

                register_trigger("vazao")

            # CLORO ALTO
            if tag_tipo == "cloro" and value > limite_cloro and should_trigger("cloro"):
                msg_console = (
                    f"⚠️ ALARME de CLORO ALTO! valor={value}, "
                    f"limite={limite_cloro}, ts={ts}, tag={tag_original}"
                )
                print("[ALERTA] Disparando:", msg_console)

                try:
                    enviar_alerta_para_destinatarios_padrao(
                        equipamento="Cloro",
                        valor_kpi=value,
                        limite=limite_cloro,
                    )
                except Exception as e:
                    print("[ERRO EMAIL] ao enviar alerta de cloro:", e)

                try:
                    enviar_alerta_whatsapp(
                        equipamento="Cloro",
                        valor_kpi=value,
                        limite=limite_cloro,
                    )
                except Exception as e:
                    print("[ERRO WPP] ao enviar alerta de cloro:", e)

                register_trigger("cloro")

            # PRESSÃO ALTA
            if tag_tipo == "pressao" and value > limite_pressao and should_trigger("pressao"):
                msg_console = (
                    f"⚠️ ALARME de PRESSÃO ALTA! valor={value}, "
                    f"limite={limite_pressao}, ts={ts}, tag={tag_original}"
                )
                print("[ALERTA] Disparando:", msg_console)

                try:
                    enviar_alerta_para_destinatarios_padrao(
                        equipamento="Pressão",
                        valor_kpi=value,
                        limite=limite_pressao,
                    )
                except Exception as e:
                    print("[ERRO EMAIL] ao enviar alerta de pressão:", e)

                try:
                    enviar_alerta_whatsapp(
                        equipamento="Pressão",
                        valor_kpi=value,
                        limite=limite_pressao,
                    )
                except Exception as e:
                    print("[ERRO WPP] ao enviar alerta de pressão:", e)

                register_trigger("pressao")

            # NÍVEL ALTO
            if tag_tipo == "nivel" and value > limite_nivel and should_trigger("nivel"):
                msg_console = (
                    f"⚠️ ALARME de NÍVEL ALTO! valor={value}, "
                    f"limite={limite_nivel}, ts={ts}, tag={tag_original}"
                )
                print("[ALERTA] Disparando:", msg_console)

                try:
                    enviar_alerta_para_destinatarios_padrao(
                        equipamento="Nível",
                        valor_kpi=value,
                        limite=limite_nivel,
                    )
                except Exception as e:
                    print("[ERRO EMAIL] ao enviar alerta de nível:", e)

                try:
                    enviar_alerta_whatsapp(
                        equipamento="Nível",
                        valor_kpi=value,
                        limite=limite_nivel,
                    )
                except Exception as e:
                    print("[ERRO WPP] ao enviar alerta de nível:", e)

                register_trigger("nivel")

    except Exception as e:
        print("[ALARM WORKER] Erro inesperado no loop principal:", e)
    finally:
        try:
            conn.close()
        except Exception:
            pass


def main():
    print("[ALARM WORKER] Iniciando loop 24/7 de verificação de alarmes...")
    while True:
        check_alerts()
        time.sleep(5)


if __name__ == "__main__":
    main()

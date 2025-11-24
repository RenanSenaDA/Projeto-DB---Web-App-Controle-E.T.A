import os
import time
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor

from alerts_email import enviar_alerta_para_destinatarios_padrao


def get_db_url():
    """
    Lê DATABASE_URL do .env e ajusta para um formato aceito pelo psycopg2.
    Ex.: postgresql+psycopg2:// -> postgresql://
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL não definido no ambiente")

    if db_url.startswith("postgresql+psycopg2://"):
        db_url = db_url.replace("postgresql+psycopg2://", "postgresql://", 1)

    return db_url


def connect():
    db_url = get_db_url()
    print("[WORKER] Conectando no Postgres via DATABASE_URL...")
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)


def alarmes_ativados(conn):
    """
    Verifica na tabela config_sistema se os alarmes estão ligados.
    """
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT alarms_enabled FROM config_sistema WHERE id = 1;")
            row = cur.fetchone()
            if not row:
                # se não tiver registro, por segurança considera ligado
                return True
            return bool(row["alarms_enabled"])
    except Exception as e:
        print("[WORKER] Erro ao ler config_sistema:", e)
        conn.rollback()
        # fallback: não bloquear o envio se der erro de leitura
        return True


def obter_medidas_criticas(conn):
    """
    Lê a view v_medidas_com_limites e retorna apenas as medidas acima do limite.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT sensor_id, tag, unit, ts, valor_atual, limite_max, acima_limite
            FROM v_medidas_com_limites
            WHERE acima_limite = TRUE;
            """
        )
        return cur.fetchall()


def pode_disparar(conn, sensor_id, cooldown_minutos=10):
    """
    Verifica na tabela log_alarmes se já foi enviado alerta para esse sensor
    dentro da janela de cooldown.
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ts
                FROM log_alarmes
                WHERE sensor_id = %s
                ORDER BY ts DESC
                LIMIT 1;
                """,
                (str(sensor_id),),
            )
            row = cur.fetchone()

        if not row:
            return True

        ultimo = row["ts"]
        agora = datetime.utcnow()
        return (agora - ultimo) >= timedelta(minutes=cooldown_minutos)

    except Exception as e:
        print("[WORKER] Erro ao verificar cooldown:", e)
        conn.rollback()
        # se der erro no cooldown, não vamos travar o alerta
        return True


def registrar_disparo(conn, sensor_id, mensagem):
    """
    Registra o disparo de um alerta na tabela log_alarmes.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO log_alarmes (sensor_id, ts, message)
            VALUES (%s, NOW(), %s);
            """,
            (str(sensor_id), mensagem),
        )
    conn.commit()


def loop_alarmas():
    print("[WORKER] Motor de alarmes iniciado. Rodando em loop...")

    while True:
        try:
            conn = connect()

            if not alarmes_ativados(conn):
                print("[WORKER] Alarmes desativados em config_sistema. Pulando ciclo.")
                conn.close()
                time.sleep(5)
                continue

            medidas = obter_medidas_criticas(conn)

            if not medidas:
                print("[WORKER] Nenhuma medida acima dos limites.")
                conn.close()
                time.sleep(5)
                continue

            for row in medidas:
                sensor_id = row["sensor_id"]
                tag = row["tag"]
                unit = row["unit"]
                ts = row["ts"]
                valor_atual = row["valor_atual"]
                limite_max = row["limite_max"]

                if not pode_disparar(conn, sensor_id):
                    print(
                        f"[WORKER] Cooldown ativo para sensor {sensor_id} ({tag}). "
                        "Alerta não será reenviado agora."
                    )
                    continue

                mensagem = (
                    f"⚠️ Alerta no sensor {tag} (ID {sensor_id})\n"
                    f"Valor atual: {valor_atual} {unit}\n"
                    f"Limite configurado: {limite_max} {unit}\n"
                    f"Horário da leitura: {ts}\n"
                )

                print("[WORKER] Disparando alerta:\n", mensagem)

                # e-mail (Brevo)
                try:
                    enviar_alerta_para_destinatarios_padrao(mensagem)
                except Exception as e:
                    print("[WORKER] Erro ao enviar alerta por e-mail:", e)

                registrar_disparo(conn, sensor_id, mensagem)

            conn.close()

        except Exception as e:
            print("[WORKER] Erro no loop de alarmes:", e)

        # intervalo entre ciclos
        time.sleep(5)


if __name__ == "__main__":
    loop_alarmas()

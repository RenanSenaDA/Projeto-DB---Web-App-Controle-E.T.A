import time
import psycopg2
import os

def connect():
    db_url = os.getenv("DATABASE_URL")
    print("[WORKER] Conectando no Postgres via DATABASE_URL...")
    return psycopg2.connect(db_url)

def main():
    print("[WORKER] Motor de alarmes iniciado. Rodando em loop...")

    while True:
        try:
            conn = connect()
            cur = conn.cursor()

            cur.execute("""
                SELECT sensor_id, tag, unit, ts, valor_atual, limite_max, acima_limite
                FROM v_medidas_com_limites
                WHERE acima_limite = TRUE;
            """)

            rows = cur.fetchall()

            for row in rows:
                sensor_id, tag, unit, ts, valor_atual, limite_max, acima_limite = row

                print("\n=== ALERTA DETECTADO ===")
                print(f"Sensor......: {sensor_id}")
                print(f"Tag.........: {tag}")
                print(f"Valor atual.: {valor_atual}")
                print(f"Limite max..: {limite_max}")
                print(f"Horário.....: {ts}")
                print("========================\n")

                # aqui você coloca envio email ou whatsapp
                # send_alert(tag, valor_atual, limite_max)

            cur.close()
            conn.close()

        except Exception as e:
            print("[WORKER] Erro no loop de alarmes:", e)

        time.sleep(5)

if __name__ == "__main__":
    main()

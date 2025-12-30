import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

from alerts_email import enviar_alerta_para_destinatarios_padrao
from alerts_whatsapp import enviar_alerta_whatsapp

from dotenv import load_dotenv, find_dotenv

# tenta achar um .env padrão no PATH
load_dotenv(find_dotenv())

# tenta também caminhos relativos ao arquivo deste worker
_base_dir = Path(__file__).resolve().parent
for extra in [
    _base_dir / ".env",
    _base_dir.parent / ".env",
    _base_dir.parent / "eta-stack" / ".env",
    _base_dir.parent / "streamlit" / ".env",
]:
    if extra.exists():
        load_dotenv(extra, override=False)


def get_db_url() -> str:
    """
    Monta a URL do Postgres.

    - Se DATABASE_URL existir, usa ela.
    - Caso contrário, monta a partir de DB_HOST/DB_PORT/POSTGRES_DB/POSTGRES_USER/POSTGRES_PASSWORD.
    """
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return url

    host = os.getenv("DB_HOST") or os.getenv("PGHOST", "localhost")
    port = os.getenv("DB_PORT") or os.getenv("PGPORT", "5432")
    user = os.getenv("POSTGRES_USER") or os.getenv("PGUSER", "postgres")
    pwd = os.getenv("POSTGRES_PASSWORD") or os.getenv("PGPASSWORD", "postgres")
    db = os.getenv("POSTGRES_DB") or os.getenv("PGDATABASE", "eta")

    return f"postgresql://{user}:{pwd}@{host}:{port}/{db}"


DB_URL = get_db_url()

# Tabela de status global (DEVE ser a MESMA do backend/API).
# Padrão recomendado: eta.config_sistema
CONFIG_SISTEMA_TABLE = (os.getenv("CONFIG_SISTEMA_TABLE", "eta.config_sistema") or "").strip()
if not CONFIG_SISTEMA_TABLE:
    CONFIG_SISTEMA_TABLE = "eta.config_sistema"

# =====================================================================
# CONFIG GERAL
# =====================================================================

COOLDOWN_MINUTES = 10
ultimo_disparo: dict[str, datetime] = {}

LIMITES_POR_TIPO_DEFAULT: dict[str, float] = {
    "ph": 7.0,
    "pressao": 5.0,
    "turbidez": 10.0,
    "cloro": 400.0,
    "vazao": 300.0,
    "nivel": 22000.0,
}

NOMES_TIPO = {
    "ph": "pH",
    "pressao": "Pressão",
    "turbidez": "Turbidez",
    "cloro": "Cloro",
    "vazao": "Vazão",
    "nivel": "Nível do Reservatório",
}

TIPO_LIMITE_ACIMA = "ACIMA"
TIPO_LIMITE_ABAIXO = "ABAIXO"

TIPO_LIMITE_POR_TIPO: dict[str, str] = {
    "ph": TIPO_LIMITE_ACIMA,
    "pressao": TIPO_LIMITE_ACIMA,
    "turbidez": TIPO_LIMITE_ACIMA,
    "cloro": TIPO_LIMITE_ACIMA,
    "vazao": TIPO_LIMITE_ACIMA,
    "nivel": TIPO_LIMITE_ACIMA,
}


def normalizar_tipo_limite(raw: str | None) -> str:
    if not raw:
        return TIPO_LIMITE_ACIMA
    raw_up = str(raw).strip().upper()
    if raw_up in ("ACIMA", "SUPERIOR", "MAIOR", ">"):
        return TIPO_LIMITE_ACIMA
    if raw_up in ("ABAIXO", "INFERIOR", "MENOR", "<"):
        return TIPO_LIMITE_ABAIXO
    return TIPO_LIMITE_ACIMA


def compara_valor_com_limite(valor_atual, limite, tipo_limite_str: str) -> bool:
    tipo_limite = normalizar_tipo_limite(tipo_limite_str)
    try:
        v = float(valor_atual)
        lim = float(limite)
    except (TypeError, ValueError):
        return False

    if tipo_limite == TIPO_LIMITE_ACIMA:
        return v > lim
    if tipo_limite == TIPO_LIMITE_ABAIXO:
        return v < lim
    return False


def montar_mensagem_extra(
    nome_parametro: str,
    tag_original: str | None,
    valor_atual,
    limite,
    tipo_limite_str: str,
) -> str:
    tipo_limite = normalizar_tipo_limite(tipo_limite_str)
    direcao = "ACIMA" if tipo_limite == TIPO_LIMITE_ACIMA else "ABAIXO"

    try:
        valor_fmt = f"{float(valor_atual):.2f}"
    except (TypeError, ValueError):
        valor_fmt = str(valor_atual)

    try:
        limite_fmt = f"{float(limite):.2f}"
    except (TypeError, ValueError):
        limite_fmt = str(limite)

    tag_info = f"Tag original: {tag_original}. " if tag_original else ""

    return (
        f"{tag_info}"
        f"Parâmetro: {nome_parametro}. "
        f"Valor atual: {valor_fmt}. Limite configurado: {limite_fmt}. "
        f"Condição do alarme: DISPARAR quando o valor estiver {direcao} do limite."
    )


# =====================================================================
# FUNÇÕES AUXILIARES
# =====================================================================

def db_connect():
    if not DB_URL:
        raise RuntimeError("URL do banco não foi definida.")
    conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
    return conn


def ensure_config_sistema_row() -> None:
    """
    Garante que exista (id=1) em CONFIG_SISTEMA_TABLE.
    """
    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(f"SELECT id FROM {CONFIG_SISTEMA_TABLE} WHERE id=1;")
        row = cur.fetchone()
        if not row:
            cur.execute(
                f"INSERT INTO {CONFIG_SISTEMA_TABLE}(id, alarms_enabled, updated_at) "
                f"VALUES (1, FALSE, now());"
            )
            conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("[ALARM WORKER] Falha ao garantir config_sistema row:", e)


def is_alarms_enabled() -> bool:
    """
    Fonte ÚNICA de verdade: eta.config_sistema.alarms_enabled (id=1).
    Fail-safe: se der erro, assume False (evita spam).
    """
    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(f"SELECT alarms_enabled FROM {CONFIG_SISTEMA_TABLE} WHERE id=1;")
        row = cur.fetchone()
        cur.close()
        conn.close()

        enabled = bool(row["alarms_enabled"]) if row and "alarms_enabled" in row else False
        print(f"[ALARM WORKER] alarms_enabled (DB) = {enabled}")
        return enabled

    except Exception as e:
        print("[ALARM WORKER] Falha ao consultar alarms_enabled no DB. Bloqueando envio (fail-safe). Erro:", e)
        return False


def get_last_measurements():
    query = """
        SELECT
            s.id AS sensor_id,
            COALESCE(m.tag, s.meta->>'tag', s.tag) AS tag,
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

    conn = db_connect()
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return rows


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


def should_trigger(tipo: str) -> bool:
    agora = datetime.now(timezone.utc)
    last = ultimo_disparo.get(tipo)
    if last is None:
        return True
    return (agora - last) >= timedelta(minutes=COOLDOWN_MINUTES)


def register_trigger(tipo: str):
    ultimo_disparo[tipo] = datetime.now(timezone.utc)


def load_limits_from_db() -> dict[str, float]:
    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute("SELECT tag, limite FROM eta.config_limites;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print("[ALARM WORKER] Erro ao carregar eta.config_limites:", e)
        return {}

    limits: dict[str, float] = {}
    for r in rows:
        tag = r.get("tag")
        limite = r.get("limite")
        if tag is None or limite is None:
            continue
        try:
            limits[tag] = float(limite)
        except (TypeError, ValueError):
            continue

    return limits


# =====================================================================
# LOOP PRINCIPAL
# =====================================================================

def check_alerts():
    print("\n[ALARM WORKER] Verificando sensores...")

    if not is_alarms_enabled():
        print("[ALARM WORKER] Alarmes DESATIVADOS. Não envia nada.")
        return

    limits_por_tag = load_limits_from_db()

    try:
        rows = get_last_measurements()
    except Exception as e:
        print("[ALARM WORKER] Erro ao buscar últimas medições:", e)
        return

    if not rows:
        print("[ALARM WORKER] Nenhuma leitura encontrada.")
        return

    for r in rows:
        sensor_id = r.get("sensor_id")
        tag_original = r.get("tag")
        value = r.get("value")
        ts = r.get("ts")

        tipo = normalizar_tipo(tag_original)
        if tipo is None:
            print(f"[DEBUG] sensor_id={sensor_id}, tag={tag_original} -> tipo não mapeado")
            continue

        limite_config_tag = None
        origem_limite = "DEFAULT_POR_TIPO"

        if tag_original in limits_por_tag:
            limite_config_tag = limits_por_tag[tag_original]
            origem_limite = f"DB (tag={tag_original})"
        else:
            for tag_cfg, lim_cfg in limits_por_tag.items():
                if normalizar_tipo(tag_cfg) == tipo:
                    limite_config_tag = lim_cfg
                    origem_limite = f"DB (por tipo tag={tag_cfg})"
                    break

        limite = limite_config_tag if limite_config_tag is not None else LIMITES_POR_TIPO_DEFAULT.get(tipo)
        if limite is None or value is None:
            continue

        tipo_limite_config = TIPO_LIMITE_POR_TIPO.get(tipo, TIPO_LIMITE_ACIMA)
        pode_disparar = should_trigger(tipo)
        condicao_alarme = compara_valor_com_limite(value, limite, tipo_limite_config)

        print(
            f"[DEBUG] sensor_id={sensor_id}, tag={tag_original}, tipo={tipo}, "
            f"value={value}, limite={limite} (origem={origem_limite}), "
            f"condicao={condicao_alarme}, cooldown_ok={pode_disparar}"
        )

        if condicao_alarme and pode_disparar:
            nome = NOMES_TIPO.get(tipo, tipo)
            msg_extra = montar_mensagem_extra(
                nome_parametro=nome,
                tag_original=tag_original,
                valor_atual=value,
                limite=limite,
                tipo_limite_str=tipo_limite_config,
            )

            print(f"[ALERTA] Disparando {nome}: valor={value}, limite={limite}, ts={ts}")

            try:
                ok_email = enviar_alerta_para_destinatarios_padrao(
                    equipamento=nome,
                    valor_kpi=f"{float(value):.2f}",
                    mensagem_extra=msg_extra,
                )
                print(f"[ALERTA-EMAIL] {nome}: {ok_email}")
            except Exception as e:
                print("[ERRO EMAIL] ao enviar alerta:", e)

            try:
                ok_wpp = enviar_alerta_whatsapp(
                    equipamento=nome,
                    valor_kpi=f"{float(value):.2f}",
                    limite=limite,
                )
                print(f"[ALERTA-WPP] {nome}: {ok_wpp}")
            except Exception as e:
                print("[ERRO WPP] ao enviar alerta:", e)

            register_trigger(tipo)


def main_loop():
    print(f"[ALARM WORKER] Motor de alarmes iniciado. Tabela de status: {CONFIG_SISTEMA_TABLE}. Loop 24/7...")
    ensure_config_sistema_row()
    while True:
        try:
            check_alerts()
        except Exception as e:
            print("[ALARM WORKER] Erro inesperado no loop principal:", e)
        time.sleep(5)


if __name__ == "__main__":
    main_loop()

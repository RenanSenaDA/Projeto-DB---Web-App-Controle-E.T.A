import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

from alerts_email import enviar_alerta_para_destinatarios_padrao
from alerts_whatsapp import enviar_alerta_whatsapp

# =====================================================================
# CARREGA .env (igual ao Streamlit)
# =====================================================================
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
    - Caso contrário, monta a partir de DB_HOST/DB_PORT/POSTGRES_DB/POSTGRES_USER/POSTGRES_PASSWORD,
      igual ao que o Streamlit faz.
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

# =====================================================================
# CONFIG GERAL
# =====================================================================

# cooldown por TIPO (ph, pressao, turbidez, cloro, vazao, nivel)
COOLDOWN_MINUTES = 10
ultimo_disparo: dict[str, datetime] = {}  # {"nivel": datetime(...), ...}

# Limites default POR TIPO (usados só se não houver limite no banco)
LIMITES_POR_TIPO_DEFAULT: dict[str, float] = {
    "ph": 7.0,
    "pressao": 5.0,
    "turbidez": 10.0,
    "cloro": 400.0,
    "vazao": 300.0,
    "nivel": 22000.0,
}

# nomes amigáveis só para logs / e-mails
NOMES_TIPO = {
    "ph": "pH",
    "pressao": "Pressão",
    "turbidez": "Turbidez",
    "cloro": "Cloro",
    "vazao": "Vazão",
    "nivel": "Nível do Reservatório",
}

# =====================================================================
# TIPO DE LIMITE (ACIMA / ABAIXO) PADRONIZADO POR TIPO
# =====================================================================

TIPO_LIMITE_ACIMA = "ACIMA"
TIPO_LIMITE_ABAIXO = "ABAIXO"

# Por enquanto todos estão como ACIMA:
#  -> dispara quando valor_atual > limite
TIPO_LIMITE_POR_TIPO: dict[str, str] = {
    "ph": TIPO_LIMITE_ACIMA,
    "pressao": TIPO_LIMITE_ACIMA,
    "turbidez": TIPO_LIMITE_ACIMA,
    "cloro": TIPO_LIMITE_ACIMA,
    "vazao": TIPO_LIMITE_ACIMA,
    "nivel": TIPO_LIMITE_ACIMA,  # Nível do reservatório: dispara QUANDO ESTIVER ACIMA do limite
}


def normalizar_tipo_limite(raw: str | None) -> str:
    """
    Converte qualquer coisa que venha do sistema para ACIMA ou ABAIXO.
    (pensado para o futuro, caso venha 'superior', 'inferior', '>', '<' etc.)
    """
    if not raw:
        return TIPO_LIMITE_ACIMA

    raw_up = str(raw).strip().upper()

    if raw_up in ("ACIMA", "SUPERIOR", "MAIOR", ">"):
        return TIPO_LIMITE_ACIMA

    if raw_up in ("ABAIXO", "INFERIOR", "MENOR", "<"):
        return TIPO_LIMITE_ABAIXO

    return TIPO_LIMITE_ACIMA


def compara_valor_com_limite(valor_atual, limite, tipo_limite_str: str) -> bool:
    """
    Regra ÚNICA de comparação de alarme.
    - Se tipo_limite == ACIMA  -> dispara quando valor_atual > limite
    - Se tipo_limite == ABAIXO -> dispara quando valor_atual < limite
    """
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
    """
    Texto adicional enviado no e-mail, já dizendo claramente
    se o alarme é para ACIMA ou ABAIXO do limite.
    """
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
    """Abre conexão com o Postgres usando DB_URL."""
    if not DB_URL:
        raise RuntimeError("URL do banco não foi definida.")
    print("[ALARM WORKER] Abrindo conexão com banco...")
    conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
    return conn


def is_alarms_enabled() -> bool:
    """
    Lê o status dos alarmes na tabela config_sistema.
    Se der erro ou não existir, assume True (para não ficar mudo).
    """
    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute("SELECT alarms_enabled FROM config_sistema WHERE id = 1;")
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row is None:
            print(
                "[ALARM WORKER] Tabela config_sistema sem registro id=1. "
                "Assumindo alarms_enabled = TRUE."
            )
            return True

        enabled = bool(row.get("alarms_enabled"))
        print(f"[ALARM WORKER] Status dos alarmes em config_sistema: {enabled}")
        return enabled

    except Exception as e:
        print(
            "[ALARM WORKER] Erro ao ler config_sistema, "
            "assumindo alarms_enabled = TRUE. Erro:",
            e,
        )
        return True


def get_last_measurements():
    """
    Busca a ÚLTIMA leitura de cada sensor na eta.measurement.

    Usa:
      - s.id    como sensor_id
      - COALESCE(m.tag, s.meta->>'tag', s.tag) como tag
      - m.value, m.ts
    """
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

    print("[ALARM WORKER] Leituras encontradas:", rows)
    return rows


def normalizar_tipo(tag_original: str | None) -> str | None:
    """
    Converte a tag original em um dos tipos padrão:
    ph, pressao, turbidez, cloro, vazao, nivel.
    """
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
    """Respeita o cooldown por tipo."""
    agora = datetime.now(timezone.utc)
    last = ultimo_disparo.get(tipo)
    if last is None:
        return True
    if agora - last >= timedelta(minutes=COOLDOWN_MINUTES):
        return True
    return False


def register_trigger(tipo: str):
    ultimo_disparo[tipo] = datetime.now(timezone.utc)


def load_limits_from_db() -> dict[str, float]:
    """
    Carrega os limites por tag da tabela eta.config_limites.
    Retorna dict: { "qualidade/ph": 7.0, "nivel/reservatorio": 23400.0, ... }
    """
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

    print("[ALARM WORKER] Limites vindos de eta.config_limites:", limits)
    return limits


# =====================================================================
# LOOP PRINCIPAL DE CHECAGEM
# =====================================================================


def check_alerts():
    print("\n[ALARM WORKER] Verificando sensores...")

    # 1) verifica se alarmes estão ligados
    if not is_alarms_enabled():
        print("[ALARM WORKER] Alarmes DESATIVADOS em config_sistema. Não dispara nada.")
        return

    # 2) carrega limites do banco (para ficar igual ao Streamlit)
    limits_por_tag = load_limits_from_db()

    # 3) lê últimas medições
    try:
        rows = get_last_measurements()
    except Exception as e:
        print("[ALARM WORKER] Erro ao buscar últimas medições:", e)
        return

    if not rows:
        print("[ALARM WORKER] Nenhuma leitura encontrada.")
        return

    # 4) processa cada sensor
    for r in rows:
        sensor_id = r.get("sensor_id")
        tag_original = r.get("tag")
        value = r.get("value")
        ts = r.get("ts")

        tipo = normalizar_tipo(tag_original)

        if tipo is None:
            print(
                f"[DEBUG] sensor_id={sensor_id}, tag_original={tag_original} "
                f"-> tipo NÃO mapeado, ignorando."
            )
            continue

        # -------------------------------------------------------------
        # Definição do LIMITE:
        # 1) tenta usar o limite da tag exata (ex.: "nivel/reservatorio")
        # 2) se não achar, tenta achar qualquer tag do mesmo TIPO (nivel, ph etc.)
        # 3) se ainda assim não tiver, cai no default por tipo
        # -------------------------------------------------------------
        limite_config_tag = None
        origem_limite = "DEFAULT_POR_TIPO"

        # 1) por tag exata
        if tag_original in limits_por_tag:
            limite_config_tag = limits_por_tag[tag_original]
            origem_limite = f"DB eta.config_limites (tag={tag_original})"
        else:
            # 2) por tipo
            for tag_cfg, lim_cfg in limits_por_tag.items():
                if normalizar_tipo(tag_cfg) == tipo:
                    limite_config_tag = lim_cfg
                    origem_limite = f"DB eta.config_limites (por tipo, tag={tag_cfg})"
                    break

        if limite_config_tag is not None:
            limite = limite_config_tag
        else:
            # 3) fallback final: limite padrão por tipo
            limite = LIMITES_POR_TIPO_DEFAULT.get(tipo)
            origem_limite = "DEFAULT_POR_TIPO"

        if limite is None:
            print(
                f"[DEBUG] sensor_id={sensor_id}, tag_original={tag_original}, "
                f"tag_tipo={tipo} -> SEM limite configurado (nem DB nem default), ignorando."
            )
            continue

        if value is None:
            print(
                f"[DEBUG] sensor_id={sensor_id}, tag_original={tag_original}, "
                f"tag_tipo={tipo} -> value=None, ignorando."
            )
            continue

        tipo_limite_config = TIPO_LIMITE_POR_TIPO.get(tipo, TIPO_LIMITE_ACIMA)
        pode_disparar = should_trigger(tipo)
        condicao_alarme = compara_valor_com_limite(value, limite, tipo_limite_config)

        print(
            f"[DEBUG] sensor_id={sensor_id}, tag_original={tag_original}, "
            f"tag_tipo={tipo}, value={value}, limite={limite} (origem={origem_limite}), "
            f"tipo_limite={tipo_limite_config}, "
            f"condicao_alarme={condicao_alarme}, pode_disparar={pode_disparar}"
        )

        if condicao_alarme and pode_disparar:
            nome = NOMES_TIPO.get(tipo, tipo)
            print(
                f"[ALERTA] Disparando ALARME de {nome}! "
                f"valor={value}, limite={limite}, ts={ts}, tag={tag_original}, "
                f"tipo_limite={tipo_limite_config}, origem_limite={origem_limite}"
            )

            # monta mensagem extra coerente com a direção ACIMA/ABAIXO
            msg_extra = montar_mensagem_extra(
                nome_parametro=nome,
                tag_original=tag_original,
                valor_atual=value,
                limite=limite,
                tipo_limite_str=tipo_limite_config,
            )

            # ===================== E-MAIL =====================
            try:
                ok_email = enviar_alerta_para_destinatarios_padrao(
                    equipamento=nome,
                    valor_kpi=f"{float(value):.2f}",
                    mensagem_extra=msg_extra,
                )
                print(f"[ALERTA-EMAIL] Resultado envio ({nome}): {ok_email}")
            except Exception as e:
                print("[ERRO EMAIL] ao enviar alerta:", e)

            # ===================== WHATSAPP =====================
            try:
                ok_wpp = enviar_alerta_whatsapp(
                    equipamento=nome,
                    valor_kpi=f"{float(value):.2f}",
                    limite=limite,
                )
                print(f"[ALERTA-WPP] Resultado envio ({nome}): {ok_wpp}")
            except Exception as e:
                print("[ERRO WPP] ao enviar alerta:", e)

            register_trigger(tipo)
        else:
            # debug para saber quando NÃO dispara
            print(
                f"[DEBUG] Sem alarme para {tipo}: "
                f"valor={value}, limite={limite} (origem={origem_limite}), "
                f"tipo_limite={tipo_limite_config}, "
                f"condicao_alarme={condicao_alarme}, "
                f"pode_disparar={pode_disparar}"
            )


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

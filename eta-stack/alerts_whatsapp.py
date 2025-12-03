import os
import json
import requests
from datetime import datetime

# -------------------------------------------------------------------
# Variáveis de ambiente (aceita nomes antigos e novos)
# -------------------------------------------------------------------

# Token de acesso (novo nome ou antigo)
WPP_ACCESS_TOKEN = os.getenv("WPP_ACCESS_TOKEN") or os.getenv("WPP_TOKEN")

# Phone Number ID
WPP_PHONE_NUMBER_ID = os.getenv("WPP_PHONE_NUMBER_ID")

# Versão da API
WPP_API_VERSION = os.getenv("WPP_API_VERSION", "v21.0")

# Template
TEMPLATE_NAME = os.getenv("WPP_TEMPLATE_NAME", "alerta_eta")
TEMPLATE_LANG = os.getenv("WPP_TEMPLATE_LANGUAGE", "pt_BR")


def _obter_destinatarios() -> list[str]:
    """
    Monta a lista de destinatários a partir das variáveis de ambiente,
    aceitando vários nomes (compatibilidade com código antigo).
    """

    candidatos_raw: list[str] = []

    # Preferência: lista padrão nova
    for var in ("WPP_DESTINATARIOS_PADRAO",
                "ALERT_WPP_RECIPIENTS",
                "WHATSAPP_DESTINO"):
        raw = os.getenv(var, "")
        if raw:
            candidatos_raw.append(raw)

    # Fallback: WPP_TO
    wpp_to = os.getenv("WPP_TO", "")
    if wpp_to:
        candidatos_raw.append(wpp_to)

    if not candidatos_raw:
        return []

    # Quebra por vírgula, tira espaços e remove duplicados
    numeros: list[str] = []
    for bloco in candidatos_raw:
        partes = [p.strip() for p in bloco.split(",") if p.strip()]
        for num in partes:
            if num not in numeros:
                numeros.append(num)

    return numeros


def enviar_alerta_whatsapp(
    parametro=None,
    valor_atual=None,
    limite=None,
    timestamp_str=None,
    equipamento=None,
    valor_kpi=None,
    **kwargs,
):
    """
    Envia alerta de WhatsApp para TODOS os números configurados em:

      WPP_DESTINATARIOS_PADRAO=5583...,5583...,5583...
      ALERT_WPP_RECIPIENTS=...
      WHATSAPP_DESTINO=...
      WPP_TO=...

    Compatível com chamadas antigas:
      enviar_alerta_whatsapp(equipamento=..., valor_kpi=..., limite=...)

    e com chamadas novas:
      enviar_alerta_whatsapp(parametro=..., valor_atual=..., limite=..., timestamp_str=...)
    """

    print("[ALERTA-WPP] Função enviar_alerta_whatsapp chamada.")

    # ---------------------------------------------------------------
    # Compatibilidade com assinatura antiga
    # ---------------------------------------------------------------
    if parametro is None and equipamento is not None:
        parametro = equipamento

    if valor_atual is None and valor_kpi is not None:
        try:
            valor_atual = float(valor_kpi)
        except Exception:
            valor_atual = valor_kpi

    if timestamp_str is None:
        timestamp_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    # ---------------------------------------------------------------
    # Monta lista de números
    # ---------------------------------------------------------------
    lista_numeros = _obter_destinatarios()

    if not lista_numeros:
        print("[ALERTA-WPP] Nenhum destinatário definido nas variáveis de ambiente.")
        return False

    print(f"[ALERTA-WPP] Destinatários detectados: {lista_numeros}")

    # ---------------------------------------------------------------
    # Checagem de envs obrigatórias
    # ---------------------------------------------------------------
    if not WPP_ACCESS_TOKEN or not WPP_PHONE_NUMBER_ID:
        print(
            "[ALERTA-WPP] Variáveis ausentes. "
            "Verifique WPP_ACCESS_TOKEN/WPP_TOKEN e WPP_PHONE_NUMBER_ID."
        )
        return False

    url = f"https://graph.facebook.com/{WPP_API_VERSION}/{WPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    # ---------------------------------------------------------------
    # Formatação segura dos valores numéricos
    # ---------------------------------------------------------------
    try:
        valor_fmt = f"{float(valor_atual):.2f}"
    except Exception:
        valor_fmt = str(valor_atual)

    try:
        limite_fmt = f"{float(limite):.2f}"
    except Exception:
        limite_fmt = str(limite)

    sucesso_total = True

    # ---------------------------------------------------------------
    # Envia para cada destinatário
    # ---------------------------------------------------------------
    for numero in lista_numeros:
        body = {
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "template",
            "template": {
                "name": TEMPLATE_NAME,
                "language": {"code": TEMPLATE_LANG},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": str(parametro)},
                            {"type": "text", "text": valor_fmt},
                            {"type": "text", "text": limite_fmt},
                            {"type": "text", "text": str(timestamp_str)},
                        ],
                    }
                ],
            },
        }

        try:
            resp = requests.post(url, headers=headers, json=body)
            print(
                f"[ALERTA-WPP] Envio para {numero} -> "
                f"{resp.status_code} / {resp.text}"
            )
            if resp.status_code != 200:
                sucesso_total = False
        except Exception as e:
            print(f"[ALERTA-WPP] Erro ao enviar para {numero}: {e}")
            sucesso_total = False

    return sucesso_total


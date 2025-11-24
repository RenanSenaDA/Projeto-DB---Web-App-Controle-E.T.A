import os
import json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

import requests


def _get_whatsapp_credentials():
    """
    Lê as credenciais da API do WhatsApp das variáveis de ambiente.

    Necessário no .env / ambiente:
      - WPP_TOKEN              -> token permanente gerado na Meta (System User)
      - WPP_PHONE_NUMBER_ID    -> ID do número exibido na tela da Meta
      - WPP_API_VERSION        -> ex: 'v21.0' (opcional, default v21.0)
    """
    token = os.getenv("WPP_TOKEN")
    phone_id = os.getenv("WPP_PHONE_NUMBER_ID")
    api_version = os.getenv("WPP_API_VERSION", "v21.0")

    if not token or not phone_id:
        print("[ALERTA-WPP] ERRO: WPP_TOKEN ou WPP_PHONE_NUMBER_ID não configurados no ambiente.")
        return None, None, None

    return token, phone_id, api_version


def _montar_mensagem(equipamento: str, valor_kpi, limite, timestamp=None) -> str:
    """
    Monta o texto padrão de alerta para envio no WhatsApp.
    Ajuste o texto de acordo com sua necessidade.
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")

    mensagem = (
        "⚠️ ALERTA ETA ⚠️\n\n"
        f"Equipamento / Parâmetro: {equipamento}\n"
        f"Valor lido: {valor_kpi}\n"
        f"Limite configurado: {limite}\n"
        f"Horário: {timestamp}\n\n"
        "Verifique o painel da ETA para mais detalhes."
    )
    return mensagem


def enviar_alerta_whatsapp(numero_destino: str, equipamento: str, valor_kpi, limite, timestamp=None) -> bool:
    """
    Envia um alerta de WhatsApp para um único número.

    :param numero_destino: número no formato 55DDDXXXXXXXX (ex: '5583999999999')
    :return: True se ok, False se erro
    """
    token, phone_id, api_version = _get_whatsapp_credentials()
    if not token or not phone_id:
        return False

    if not numero_destino:
        print("[ALERTA-WPP] ERRO: número de destino vazio.")
        return False

    url = f"https://graph.facebook.com/{api_version}/{phone_id}/messages"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    corpo_mensagem = _montar_mensagem(equipamento, valor_kpi, limite, timestamp)

    payload = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": corpo_mensagem,
        },
    }

    print(f"[ALERTA-WPP] Enviando mensagem para {numero_destino}...")
    # print(f"[ALERTA-WPP] Payload: {json.dumps(payload, ensure_ascii=False)}")  # se quiser debugar

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
    except requests.RequestException as e:
        print(f"[ALERTA-WPP] ERRO de conexão ao enviar alerta: {e}")
        return False

    status = response.status_code
    try:
        resposta_json = response.json()
    except ValueError:
        resposta_json = {"raw": response.text}

    if 200 <= status < 300:
        print(f"[ALERTA-WPP] SUCESSO - Status {status} -> {resposta_json}")
        return True
    else:
        print(f"[ALERTA-WPP] FALHA - Status {status} -> {resposta_json}")

        # tratamento específico para erro clássico de sandbox:
        # (#131030) Recipient phone number not in allowed list
        error_data = resposta_json.get("error", {})
        code = error_data.get("code")
        if code == 131030:
            print(
                "[ALERTA-WPP] ATENÇÃO: Número de destino não está na lista permitida "
                "(sandbox). Adicione o número na tela da Meta ou use um número em produção."
            )

        return False


def enviar_alerta_whatsapp_para_destinatarios_padrao(
    equipamento: str, valor_kpi, limite, timestamp=None
) -> bool:
    """
    Envia alerta de WhatsApp para uma lista padrão de destinatários.

    Ordem de preferência das variáveis de ambiente:

      1. WPP_DESTINATARIOS_PADRAO  -> formato: 5583...,5583...
      2. ALERT_WPP_RECIPIENTS      -> compatibilidade com código antigo
      3. WHATSAPP_DESTINO          -> um único número (herança antiga)

    Retorna True se pelo menos um envio ocorrer com sucesso.
    """

    # 1) Tenta pegar da variável nova
    numeros_raw = os.getenv("WPP_DESTINATARIOS_PADRAO")

    # 2) Se não tiver, tenta das antigas (compat)
    if not numeros_raw:
        numeros_raw = os.getenv("ALERT_WPP_RECIPIENTS")

    # 3) Se ainda não tiver, tenta WHATSAPP_DESTINO (um número só)
    if not numeros_raw:
        numeros_raw = os.getenv("WHATSAPP_DESTINO")

    if not numeros_raw:
        print(
            "[ALERTA-WPP] Nenhum destinatário configurado em "
            "WPP_DESTINATARIOS_PADRAO/ALERT_WPP_RECIPIENTS/WHATSAPP_DESTINO."
        )
        return False

    # Normaliza: pode ser separado por vírgula ou ponto e vírgula
    numeros = []
    for parte in numeros_raw.replace(";", ",").split(","):
        parte = parte.strip()
        if parte:
            numeros.append(parte)

    if not numeros:
        print("[ALERTA-WPP] Lista de destinatários vazia após parsing.")
        return False

    algum_sucesso = False
    for numero in numeros:
        ok = enviar_alerta_whatsapp(numero, equipamento, valor_kpi, limite, timestamp)
        if ok:
            algum_sucesso = True

    return algum_sucesso



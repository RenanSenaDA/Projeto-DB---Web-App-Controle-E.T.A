import os
import requests
from datetime import datetime, timezone


def _get_whatsapp_credentials():
    """
    Lê as credenciais da API do WhatsApp Cloud API a partir do .env
    """
    token = os.getenv("WHATSAPP_TOKEN") or os.getenv("WPP_ACCESS_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_ID") or os.getenv("WPP_PHONE_NUMBER_ID")

    if not token or not phone_id:
        print("[ALERTA-WPP] WHATSAPP_TOKEN/WHATSAPP_PHONE_ID não configurados.")
        return None, None

    return token, phone_id


def enviar_alerta_whatsapp(
    numero_destino: str,
    equipamento: str,
    valor_kpi: str,
    limite: float,
    timestamp: str | None = None,
) -> bool:
    """
    Envia uma mensagem de alerta via WhatsApp Cloud API para um único número.
    """
    token, phone_id = _get_whatsapp_credentials()
    if not token or not phone_id:
        return False

    if not timestamp:
        timestamp = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S")

    url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    texto = (
        "🚨 *Alerta ETA - Environquip*\n\n"
        f"O equipamento *{equipamento}* ultrapassou o limite configurado.\n"
        f"Valor atual do KPI: *{valor_kpi}* (limite: {limite:.2f}).\n"
        f"Última leitura: {timestamp}.\n\n"
        "Por favor, verifique imediatamente o painel da ETA."
    )

    payload = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "text",
        "text": {"body": texto},
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"[ALERTA-WPP] Status {resp.status_code} -> {resp.text}")
        return resp.status_code in (200, 201)
    except Exception as e:
        print(f"[ALERTA-WPP] Erro ao enviar WhatsApp para {numero_destino}: {e}")
        return False


def enviar_alerta_whatsapp_para_destinatarios_padrao(
    equipamento: str,
    valor_kpi: str,
    limite: float,
    timestamp: str | None = None,
) -> bool:
    """
    Envia o alerta para todos os números configurados em ALERT_WPP_RECIPIENTS.
    Retorna True se pelo menos um envio deu certo.
    """
    dest_raw = os.getenv("ALERT_WPP_RECIPIENTS") or os.getenv("WHATSAPP_DESTINO", "")
    if not dest_raw:
        print("[ALERTA-WPP] Nenhum destinatário configurado em ALERT_WPP_RECIPIENTS/WHATSAPP_DESTINO.")
        return False

    numeros = [d.strip() for d in dest_raw.split(",") if d.strip()]
    if not numeros:
        print("[ALERTA-WPP] Lista de destinatários vazia após parsing.")
        return False

    algum_sucesso = False
    for numero in numeros:
        ok = enviar_alerta_whatsapp(numero, equipamento, valor_kpi, limite, timestamp)
        if ok:
            algum_sucesso = True

    return algum_sucesso


if __name__ == "__main__":
    # Teste rápido via linha de comando
    print("Teste de envio WhatsApp...")
    enviar_alerta_whatsapp_para_destinatarios_padrao(
        equipamento="qualidade/cloro",
        valor_kpi="3.50 mg/L",
        limite=2.0,
        timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    )

import os
import requests
import json

# Variáveis de ambiente
WPP_ACCESS_TOKEN = os.getenv("WPP_ACCESS_TOKEN")
WPP_PHONE_NUMBER_ID = os.getenv("WPP_PHONE_NUMBER_ID")
WPP_TO = os.getenv("WPP_TO")  # número destino em formato internacional, ex: 5583999999999

# Nome e idioma do template aprovado na Meta
TEMPLATE_NAME = "alerta_eta"   # exatamente o nome do modelo lá na Meta
TEMPLATE_LANG = "pt_BR"        # idioma do modelo


def enviar_alerta_whatsapp(parametro, valor_atual, limite, timestamp_str):
    """
    Envia alerta de WhatsApp usando o template 'alerta_eta' com 4 variáveis:
      {{1}} -> nome do parâmetro (ex: 'pH', 'Cloro', 'Nível Reservatório')
      {{2}} -> valor atual
      {{3}} -> limite configurado
      {{4}} -> data/hora da leitura (string)
    """

    if not (WPP_ACCESS_TOKEN and WPP_PHONE_NUMBER_ID and WPP_TO):
        print("[ALERTA-WPP] Variáveis de ambiente ausentes. Verifique WPP_ACCESS_TOKEN, WPP_PHONE_NUMBER_ID e WPP_TO.")
        return

    url = f"https://graph.facebook.com/v21.0/{WPP_PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    body = {
        "messaging_product": "whatsapp",
        "to": WPP_TO,
        "type": "template",
        "template": {
            "name": TEMPLATE_NAME,
            "language": {"code": TEMPLATE_LANG},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(parametro)},
                        {"type": "text", "text": f"{valor_atual:.2f}"},
                        {"type": "text", "text": f"{limite:.2f}"},
                        {"type": "text", "text": str(timestamp_str)},
                    ],
                }
            ],
        },
    }

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(body))
        print(f"[ALERTA-WPP] Status {resp.status_code} -> {resp.text}")
    except Exception as e:
        print(f"[ALERTA-WPP] Erro ao enviar mensagem: {e}")

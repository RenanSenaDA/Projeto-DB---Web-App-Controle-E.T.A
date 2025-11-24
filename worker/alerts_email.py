import os
import requests

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def enviar_alerta_email(email_destino, equipamento, valor_kpi, mensagem_extra=None):
    """
    Envia um e-mail de alerta crítico via Brevo.
    Retorna True se enviado com sucesso, False caso contrário.
    """

    chave_api = os.getenv("BREVO_API_KEY")
    sender_email = os.getenv("ALERT_SENDER_EMAIL", "no-reply@seu-dominio.com")
    sender_name = os.getenv("ALERT_SENDER_NAME", "Sistema Environquip")

    if not chave_api:
        print("[ALERTA-EMAIL] ERRO: BREVO_API_KEY não configurada!")
        return False

    assunto = f"ALERTA CRÍTICO: {equipamento}"

    html_content = f"""
    <h1>Alerta de Manutenção</h1>
    <p>O equipamento <strong>{equipamento}</strong> ultrapassou o limite configurado.</p>
    <p>Valor atual do KPI: <strong>{valor_kpi}</strong>.</p>
    """

    if mensagem_extra:
        html_content += f"<p>Detalhes: {mensagem_extra}</p>"

    html_content += "<p>Por favor, verifique imediatamente o painel da ETA.</p>"

    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": email_destino}],
        "subject": assunto,
        "htmlContent": html_content,
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": chave_api,
    }

    try:
        response = requests.post(BREVO_API_URL, json=payload, headers=headers)

        print(f"[ALERTA-EMAIL] Status da Notificação: {response.status_code}")
        print(f"[ALERTA-EMAIL] Resposta da API: {response.text}")

        if response.status_code in (200, 201, 202):
            return True

        return False

    except Exception as e:
        print(f"[ALERTA-EMAIL] Exceção ao enviar e-mail: {e}")
        return False


def enviar_alerta_para_destinatarios_padrao(equipamento, valor_kpi, mensagem_extra=None):
    """
    Lê a lista ALERT_DEFAULT_RECIPIENTS e envia o alerta para todos.
    """
    emails_raw = os.getenv("ALERT_DEFAULT_RECIPIENTS", "")
    emails = [e.strip() for e in emails_raw.split(",") if e.strip()]

    if not emails:
        print("[ALERTA-EMAIL] Nenhum destinatário configurado em ALERT_DEFAULT_RECIPIENTS.")
        return False

    ok_geral = True
    for email in emails:
        ok = enviar_alerta_email(email, equipamento, valor_kpi, mensagem_extra)
        ok_geral = ok_geral and ok

    return ok_geral

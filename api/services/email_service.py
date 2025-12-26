"""
Módulo de serviço de e-mail.

Responsável pelo envio de e-mails transacionais (como convites) usando a API da Brevo.
"""

import requests
from datetime import datetime
from fastapi import HTTPException   
from core.config import settings

def send_brevo_invite(to_email: str, invite_link: str):
    """
    Envia um e-mail de convite usando a API da Brevo.

    Args:
        to_email (str): Endereço de e-mail do destinatário.
        invite_link (str): URL completa para aceitar o convite.

    Raises:
        HTTPException: Se ocorrer um erro ao comunicar com a API da Brevo.
    """
    if not settings.BREVO_API_KEY:
        print("AVISO: BREVO_API_KEY não configurada. E-mail não enviado.")
        return

    payload = {
        "sender": {"name": settings.ALERT_SENDER_NAME, "email": settings.ALERT_SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": "Convite para acessar o Aqualink-EQ",
        "htmlContent": f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: sans-serif; background-color: #f4f4f5; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: #fff; padding: 20px; border-radius: 8px;">
                <h2 style="color: #0075A9;">Bem-vindo ao Aqualink EQ</h2>
                <p>Você foi convidado para criar uma conta operacional.</p>
                <a href="{invite_link}" style="background-color: #00B2E2; color: #fff; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Aceitar Convite</a>
                <p style="font-size: 12px; color: #999; margin-top: 20px;">Link expira em 24h. {datetime.now().year}</p>
            </div>
        </body>
        </html>
        """
    }
    
    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email", 
            json=payload, 
            headers={"accept": "application/json", "content-type": "application/json", "api-key": settings.BREVO_API_KEY}
        )
        response.raise_for_status()
    except Exception as e:
        print(f"Erro Brevo: {e}")
        raise HTTPException(status_code=500, detail="Erro ao enviar e-mail de convite.")
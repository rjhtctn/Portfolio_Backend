# helpers/email_sender.py

import aiosmtplib
from email.message import EmailMessage
from core.config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASS, SENDER_NAME

async def send_email_async(to_email: str, subject: str, body: str):
    message = EmailMessage()
    message["From"] = f"{SENDER_NAME} <{SMTP_USER}>"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            start_tls=True,
            username=SMTP_USER,
            password=SMTP_PASS
        )
        print(f"📧 E-posta gönderildi: {to_email}")
    except Exception as e:
        import traceback
        print(f"❌ E-posta gönderilemedi: {e}")
        traceback.print_exc()
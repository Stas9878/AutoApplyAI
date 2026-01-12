import smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from src.settings import settings
from src.logger import logger


def send_email(to_email: str, subject: str, body: str, pdf_path: Path | None = None) -> bool:
    """Отправляет email через SMTP."""
    try:
        if settings.email_port == 465:
            server = smtplib.SMTP_SSL(settings.email_host, settings.email_port)
        else:
            server = smtplib.SMTP(settings.email_host, settings.email_port)
            server.starttls()

        server.login(settings.email_user, settings.email_password)
        msg = MIMEMultipart()
        msg['From'] = settings.email_user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        if pdf_path and pdf_path.exists():
            with open(pdf_path, 'rb') as f:
                part = MIMEApplication(f.read(), _subtype='pdf')
                part.add_header('Content-Disposition', 'attachment', filename='Резюме.pdf')
                msg.attach(part)

        server.sendmail(settings.email_user, to_email, msg.as_string())
        server.quit()
        return True

    except Exception as e:
        logger.error(f'❌ Ошибка отправки на {to_email}: {e}')
        return False
import aiosmtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from src.core.settings import settings
from src.core.logger import logger


async def send_email(to_email: str, subject: str, body: str, pdf_path: Path | None = None) -> bool:
    try:
        # Создаём письмо
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

        # Отправляем через aiosmtplib
        await aiosmtplib.send(
            msg,
            hostname=settings.email_host,
            port=settings.email_port,
            username=settings.email_user,
            password=settings.email_password,
            use_tls=settings.email_port == 465,
            start_tls=settings.email_port != 465,
        )

        logger.info(f'📧 SMTP успешная отправка резюме на {to_email}')
        return True

    except aiosmtplib.SMTPRecipientsRefused as e:
        logger.warning(f'📧 SMTP отклонил получателя {to_email}: {e}')
        return False
    except aiosmtplib.SMTPException as e:
        logger.error(f'📧 SMTP ошибка при отправке на {to_email}: {e}')
        return False
    except Exception as e:
        logger.error(f'❌ Неизвестная ошибка отправки на {to_email}: {e}')
        return False
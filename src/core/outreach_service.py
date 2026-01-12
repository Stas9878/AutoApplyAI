import asyncio
from pathlib import Path
from sqlmodel import select
from datetime import datetime, timezone

from src.logger import logger
from src.settings import settings
from src.db.models import ActiveContact
from src.db.session import get_db_session
from src.core.email_sender import send_email


async def send_outreach_batch(batch_size: int = 20, pause_sec: int = 300) -> int:
    """Отправляет один батч писем."""
    pdf_path = Path(settings.resume_pdf_path)
    template_path = Path('data/cover_letter.txt')

    if not template_path.exists():
        logger.error('Файл шаблона не найден: data/cover_letter.txt')
        return 0

    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    async with get_db_session() as session:
        # Получаем контакты без статуса
        stmt = (
            select(ActiveContact)
            .where(ActiveContact.outreach_status == None)
            .limit(batch_size)
        )
        result = await session.exec(stmt)
        contacts = result.all()
        if not contacts:
            logger.info('📭 Нет контактов для отправки')
            return 0

        sent_count = 0
        for contact in contacts:
            body = template.format(company_name=contact.company_name)
            subject = 'Резюме Python-разработчика'
            success = send_email(contact.email, subject, body, pdf_path)

            # Обновляем статус
            contact.outreach_status = 'sent' if success else 'failed'
            if success:
                contact.sent_at = datetime.now()
                sent_count += 1

            session.add(contact)
            await session.commit()

            # Пауза между письмами
            await asyncio.sleep(1)

        logger.info(f'✅ Отправлено {sent_count} писем из {len(contacts)}')

        if sent_count > 0 and pause_sec > 0:
            logger.info(f'⏳ Пауза {pause_sec} секунд...')
            await asyncio.sleep(pause_sec)

        return sent_count
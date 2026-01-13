import asyncio
from pathlib import Path
from sqlmodel import select
from datetime import datetime, timezone

from src.logger import logger
from src.settings import settings
from src.db.models import ActiveContact
from src.db.session import get_db_session
from src.core.agents import CoverLetterCrew
from src.core.email_sender import send_email


async def send_outreach_batch(batch_size: int, pause_sec: int) -> int:
    """Отправляет батч писем с генерацией через CrewAI."""
    pdf_path = Path(settings.resume_pdf_path)
    crew = CoverLetterCrew()  # инициализируем агентов

    async with get_db_session() as session:
        # Получаем контакты без статуса
        stmt = select(ActiveContact).where(ActiveContact.outreach_status == None).limit(batch_size)
        result = await session.exec(stmt)
        contacts = result.all()

        if not contacts:
            logger.info('📭 Нет контактов для отправки')
            return 0

        sent_count = 0
        for contact in contacts:
            logger.info(f'✍️ Генерация письма для {contact.company_name} ({contact.email})')

            # Генерация письма
            letter = await crew.generate_letter(contact.company_name)
            if not letter:
                logger.warning(f'⚠️ Пропускаем {contact.email} — не удалось сгенерировать письмо')
                contact.outreach_status = 'failed'
                session.add(contact)
                continue

            # Отправка
            subject = 'Резюме Python-разработчика'
            success = send_email(contact.email, subject, letter, pdf_path)

            # Обновление статуса
            contact.outreach_status = 'sent' if success else 'failed'
            if success:
                contact.sent_at = datetime.now()
                sent_count += 1

            session.add(contact)
            await session.commit()
            logger.info(f'{"✅ Отправлено" if success else "❌ Не отправлено"} на {contact.email}')

            # Пауза между письмами (1–2 сек)
            await asyncio.sleep(2)

        logger.info(f'✅ Батч завершён: {sent_count}/{len(contacts)} писем отправлено')

        if sent_count > 0 and pause_sec > 0:
            logger.info(f'⏳ Пауза {pause_sec} секунд перед следующим батчем...')
            await asyncio.sleep(pause_sec)

        return sent_count
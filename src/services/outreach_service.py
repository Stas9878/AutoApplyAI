import asyncio
from pathlib import Path
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.logger import logger
from src.core.settings import settings
from src.services.agents import CoverLetterCrew
from src.db.crud import get_sent_count_last_24h
from src.services.email_sender import send_email
from src.db.crud import (
    get_pending_contacts,
    mark_contact_as_failed,
    mark_contact_as_sent
)


class OutreachState:
    def __init__(self):
        self.is_running = False
        self.started_at: datetime | None = None

    def start(self):
        self.is_running = True
        self.started_at = datetime.now()


    def stop(self):
        self.is_running = False
        self.started_at = None


outreach_state = OutreachState()


async def send_outreach_batch(session: AsyncSession, batch_size: int) -> int:
    outreach_state.start()

    try:
        contacts = await get_pending_contacts(session, limit=batch_size)
        if not contacts:
            logger.info('📭 Нет контактов для отправки')
            return 0

        pdf_path = Path(settings.resume_pdf_path)
        crew = CoverLetterCrew()
        sent_count = 0

        today_sent_count = await get_sent_count_last_24h(session)
        for contact in contacts:

            if today_sent_count + sent_count >= settings.max_emails_per_24h:
                break

            logger.info(f'✍️ Генерация письма для {contact.company_name} ({contact.email})')
            letter = await crew.generate_letter(contact.company_name)

            if not letter:
                await mark_contact_as_failed(session, contact)
                continue

            subject = 'Резюме Python-разработчика'
            success = await send_email(contact.email, subject, letter, pdf_path)

            if success:
                await mark_contact_as_sent(session, contact)
                sent_count += 1
            else:
                await mark_contact_as_failed(session, contact)

        logger.info(f'✅ Отправлено {sent_count} писем')
        return sent_count
    finally:
        outreach_state.stop()

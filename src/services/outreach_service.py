import asyncio
from pathlib import Path
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.logger import logger
from src.core.settings import settings
from src.services.agents import CoverLetterCrew
from src.services.email_sender import send_email
from src.db.crud import (
    get_pending_contacts,
    mark_contact_as_failed,
    mark_contact_as_sent
)


async def send_outreach_batch(session: AsyncSession, batch_size: int) -> int:
    contacts = await get_pending_contacts(session, limit=batch_size)
    if not contacts:
        logger.info('📭 Нет контактов для отправки')
        return 0

    pdf_path = Path(settings.resume_pdf_path)
    crew = CoverLetterCrew()
    sent_count = 0

    for contact in contacts:
        logger.info(f'✍️ Генерация письма для {contact.company_name} ({contact.email})')
        letter = await crew.generate_letter(contact.company_name)

        if not letter:
            await mark_contact_as_failed(session, contact)
            continue

        subject = 'Резюме Python-разработчика'
        success = send_email(contact.email, subject, letter, pdf_path)

        if success:
            await mark_contact_as_sent(session, contact)
            sent_count += 1
        else:
            await mark_contact_as_failed(session, contact)

        await asyncio.sleep(2)  # вежливая пауза

    logger.info(f'✅ Отправлено {sent_count} писем')
    return sent_count
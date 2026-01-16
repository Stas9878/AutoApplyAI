from sqlmodel import select
from datetime import datetime, timedelta
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import ActiveContact


async def get_sent_count_last_24h(session: AsyncSession) -> int:
    '''Возвращает количество отправленных писем за последние 24 часа.'''
    cutoff = datetime.now() - timedelta(hours=24)
    statement = select(ActiveContact).where(
        ActiveContact.outreach_status == 'sent',
        ActiveContact.sent_at >= cutoff
    )
    result = await session.exec(statement)
    return len(result.all())


async def get_oldest_sent_time(session: AsyncSession) -> datetime | None:
    '''Возвращает время самой ранней отправки за последние 24 часа.'''
    statement = (
        select(ActiveContact.sent_at)
        .where(ActiveContact.outreach_status == 'sent')
        .order_by(ActiveContact.sent_at.asc())
    )
    result = await session.exec(statement)
    return result.first()


async def get_pending_contacts(session: AsyncSession, limit: int):
    '''Получает контакты со статусом NULL (ожидающие отправки).'''
    statement = (
        select(ActiveContact)
        .where(ActiveContact.outreach_status == None)
        .limit(limit)
    )
    result = await session.exec(statement)
    return result.all()


async def mark_contact_as_sent(session: AsyncSession, contact: ActiveContact, letter: str):
    '''Помечает контакт как успешно отправленный.'''
    contact.outreach_status = 'sent'
    contact.sent_at = datetime.now()
    contact.letter = letter
    session.add(contact)
    await session.commit()


async def mark_contact_as_failed(session: AsyncSession, contact: ActiveContact, letter: str):
    '''Помечает контакт как неудачная попытка отправки.'''
    contact.outreach_status = 'failed'
    contact.letter = letter
    session.add(contact)
    await session.commit()


async def get_recently_sent_companies(session: AsyncSession):
    '''Получает список компаний, которым отправляли письма за последние 24 часа.'''
    statement = (
        select(ActiveContact)
        .where(ActiveContact.sent_at >= datetime.now() - timedelta(hours=24))
        .order_by(ActiveContact.sent_at.desc())
    )
    result = await session.exec(statement)
    return result.all()
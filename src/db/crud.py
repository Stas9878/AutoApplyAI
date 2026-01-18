from sqlmodel import select
from datetime import datetime, timedelta
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import HHVacancy, ActiveContact


# Рассылка резюме по Email
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


# Вакансии на HH
async def save_vacancy(session: AsyncSession, vacancy_data: dict) -> HHVacancy:
    '''Сохраняет или обновляет вакансию.'''
    stmt = select(HHVacancy).where(HHVacancy.id == vacancy_data['id'])
    result = await session.exec(stmt)
    existing = result.one_or_none()

    if existing:
        for key, value in vacancy_data.items():
            setattr(existing, key, value)
        existing.updated_at = datetime.now()
    else:
        existing = HHVacancy(**vacancy_data)
        session.add(existing)

    await session.commit()
    await session.refresh(existing)
    return existing


async def get_unreported_vacancies(session: AsyncSession, limit: int) -> list[HHVacancy]:
    '''Получает новые (не показанные) вакансии.'''
    stmt = (
        select(HHVacancy)
        .where(HHVacancy.is_reported == False)
        .order_by(HHVacancy.created_at.desc())
        .limit(limit)
    )
    result = await session.exec(stmt)
    return result.all()


async def mark_vacancies_as_reported(session: AsyncSession, vacancy_ids: list[str]) -> None:
    '''Помечает вакансии как показанные.'''
    from sqlalchemy import update
    stmt = (
        update(HHVacancy)
        .where(HHVacancy.id.in_(vacancy_ids))
        .values(is_reported=True, updated_at=datetime.now())
    )
    await session.exec(stmt)
    await session.commit()


async def get_recent_vacancies(session: AsyncSession, limit: int) -> list[HHVacancy]:
    '''Получает последние вакансии (включая уже показанные).'''
    stmt = (
        select(HHVacancy)
        .order_by(HHVacancy.created_at.desc())
        .limit(limit)
    )
    result = await session.exec(stmt)
    return result.all()
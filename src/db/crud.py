from uuid import UUID
from sqlmodel import select
from datetime import datetime, timedelta
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import (
    HHVacancy,
    ActiveContact,
    User,
    UserResume,
    UserSearchFilter,
    SentVacancyLog
)


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


# --- Пользователи ---
async def get_active_users_with_resume_and_filter(session: AsyncSession):
    stmt = (
        select(User, UserResume, UserSearchFilter)
        .join(UserResume, User.uuid == UserResume.user_uuid)
        .join(UserSearchFilter, User.uuid == UserSearchFilter.user_uuid)
        .where(
            User.is_active == True,
            UserSearchFilter.is_active == True
        )
    )
    result = await session.exec(stmt)
    return result.all()


# --- Резюме ---
async def save_or_update_user_resume(
    session: AsyncSession,
    user_uuid: UUID,
    resume_text: str
) -> UserResume:
    stmt = select(UserResume).where(UserResume.user_uuid == user_uuid)
    result = await session.exec(stmt)
    existing = result.one_or_none()

    if existing:
        existing.text = resume_text
        existing.updated_at = datetime.now()
    else:
        existing = UserResume(user_uuid=user_uuid, text=resume_text)
        session.add(existing)

    await session.commit()
    await session.refresh(existing)
    return existing


# --- Фильтры ---
async def save_or_update_user_filter(
    session: AsyncSession,
    user_uuid: UUID,
    **filter_data
) -> UserSearchFilter:
    stmt = select(UserSearchFilter).where(UserSearchFilter.user_uuid == user_uuid)
    result = await session.exec(stmt)
    existing = result.one_or_none()

    if existing:
        for key, value in filter_data.items():
            setattr(existing, key, value)
        existing.updated_at = datetime.now()
    else:
        existing = UserSearchFilter(user_uuid=user_uuid, **filter_data)
        session.add(existing)

    await session.commit()
    await session.refresh(existing)
    return existing


# --- Вакансии ---
async def save_vacancy_if_not_exists(
    session: AsyncSession,
    vacancy_data: dict
) -> HHVacancy:
    stmt = select(HHVacancy).where(HHVacancy.id == vacancy_data['id'])
    result = await session.exec(stmt)
    existing = result.one_or_none()

    if not existing:
        existing = HHVacancy(**vacancy_data)
        session.add(existing)
        await session.commit()
        await session.refresh(existing)
    return existing


# --- Лог отправки ---
async def has_user_seen_vacancy(
    session: AsyncSession,
    user_uuid: UUID,
    vacancy_id: str
) -> bool:
    stmt = select(SentVacancyLog).where(
        SentVacancyLog.user_uuid == user_uuid,
        SentVacancyLog.vacancy_id == vacancy_id
    )
    result = await session.exec(stmt)
    return result.one_or_none() is not None


async def mark_vacancy_as_sent_to_user(
    session: AsyncSession,
    user_uuid: UUID,
    vacancy_id: str
):
    log = SentVacancyLog(user_uuid=user_uuid, vacancy_id=vacancy_id)
    session.add(log)
    await session.commit()
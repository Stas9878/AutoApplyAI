from sqlmodel import select

from src.logger import logger
from src.db.session import get_db_session
from src.platforms.habr.parser import HabrParser
from src.db.models import ActiveContact, DeletedContact


async def parse_and_save_habr_contacts() -> dict:
    """Полная синхронизация контактов с Habr Career."""
    parser = HabrParser()
    fresh_contacts = await parser.parse_emails()
    fresh_emails = {c['email'] for c in fresh_contacts}

    async with get_db_session() as session:
        # 1. Получаем ВСЕ активные контакты за один запрос
        active_result = await session.exec(select(ActiveContact))
        active_list = active_result.all()
        active_emails = {c.email for c in active_list}

        # 2. Новые контакты → добавляем в active
        new_contacts = [
            c for c in fresh_contacts if c['email'] not in active_emails
        ]
        for contact_data in new_contacts:
            contact = ActiveContact(**contact_data)
            session.add(contact)
        await session.commit()  # Сохраняем новые

        # 3. Удалённые → переносим в deleted
        deleted_emails = active_emails - fresh_emails
        deleted_count = 0

        if deleted_emails:
            # Получаем полные объекты удалённых контактов
            deleted_active = [
                c for c in active_list if c.email in deleted_emails
            ]
            for active in deleted_active:
                # Создаём запись в deleted_contact
                deleted = DeletedContact(
                    email=active.email,
                    company_name=active.company_name,
                    source_url=active.source_url,
                    parsed_at=active.parsed_at
                )
                session.add(deleted)
                # Удаляем из active
                await session.delete(active)
                deleted_count += 1
            await session.commit()

        total_active = len(fresh_emails)
        new_count = len(new_contacts)

        logger.info(
            f'🔄 Синхронизация завершена. '
            f'Активных: {total_active}, новых: {new_count}, удалённых: {deleted_count}'
        )

        return {
            'total_active': total_active,
            'new_saved': new_count,
            'deleted_moved': deleted_count
        }
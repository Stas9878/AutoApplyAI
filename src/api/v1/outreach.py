from typing import Annotated
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.settings import settings
from src.db.session import get_db_session
from src.services.outreach_service import send_outreach_batch
from src.db.crud import get_sent_count_last_24h, get_oldest_sent_time

outreach_router = APIRouter(prefix='/outreach', tags=['Outreach'])


@outreach_router.post('/send')
async def trigger_outreach(
    background_tasks: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(get_db_session)]
):
    '''Запуск рассылки резюме'''
    sent_count = await get_sent_count_last_24h(session)

    if sent_count >= settings.max_emails_per_24h:
        oldest_sent = await get_oldest_sent_time(session)
        if oldest_sent:
            next_available = oldest_sent + timedelta(hours=24)
            now = datetime.now()
            wait_time = next_available - now
            hours, remainder = divmod(wait_time.total_seconds(), 3600)
            minutes = remainder // 60
            message = f'Лимит исчерпан. Следующая отправка возможна через {int(hours)} ч {int(minutes)} мин.'
        else:
            message = 'Лимит исчерпан. Попробуйте завтра.'

        return {
            'status': 'limit_exceeded',
            'sent_count': sent_count,
            'max_allowed': settings.max_emails_per_24h,
            'message': message
        }

    # Запускаем фоновую задачу с новой сессией
    async def _send():
        from src.db.session import get_db_session
        async with get_db_session() as bg_session:
            await send_outreach_batch(bg_session, batch_size=5)

    background_tasks.add_task(_send)

    return {
        'status': 'started',
        'message': f'Рассылка запущена. Отправлено ранее: {sent_count}/{settings.max_emails_per_24h}'
    }
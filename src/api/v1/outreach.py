from fastapi import HTTPException
from datetime import datetime, timedelta
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import APIRouter, Depends, BackgroundTasks

from src.core.settings import settings
from src.db.session import get_db_session
from src.services.agents import CoverLetterCrew
from src.services.outreach_service import send_outreach_batch, outreach_state
from src.db.crud import (
    get_sent_count_last_24h,
    get_oldest_sent_time,
    get_recently_sent_companies
)
from src.api.v1.schemas.outreach import (
    SendOutreachResponse,
    GenerateLetterRequest,
    GenerateLetterResponse,
    StatusOutreachResponse
)

outreach_router = APIRouter(prefix='/outreach', tags=['Outreach'])


@outreach_router.post('/send')
async def trigger_outreach(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session)
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

        return SendOutreachResponse(
            status='limit_exceeded',
            message=message,
            sent_count=sent_count,
            max_allowed=settings.max_emails_per_24h
        )

    # Запускаем фоновую задачу
    background_tasks.add_task(send_outreach_batch, session, batch_size=10)

    return SendOutreachResponse(
        status='started',
        message=f'Рассылка запущена. Отправлено ранее: {sent_count}/{settings.max_emails_per_24h}',
        sent_count=sent_count,
        max_allowed=settings.max_emails_per_24h
    )


@outreach_router.get('/status', response_model=StatusOutreachResponse)
async def get_outreach_status(session: AsyncSession = Depends(get_db_session)):
    '''Справочная информация о рассылке'''
    sent_count = await get_sent_count_last_24h(session)
    recent_companies = await get_recently_sent_companies(session)

    recently_sent_to = {}
    for contact in recent_companies:
        recently_sent_to[contact.email] = {
            'company_name': contact.company_name,
            'sent_at': contact.sent_at
        }

    return StatusOutreachResponse(
        is_running=outreach_state.is_running,
        should_stop=outreach_state.stop_event.is_set(),
        started_at=outreach_state.started_at,
        sent_count=sent_count,
        max_allowed=settings.max_emails_per_24h,
        recently_sent_to=recently_sent_to
    )


@outreach_router.get('/stop_send')
async def stop_outreach():
    '''Принудительно останавливает активную рассылку.'''
    if not outreach_state.is_running:
        return {
            'status': 'idle',
            'message': 'Активная рассылка не найдена'
        }

    outreach_state.stop_event.set()
    return {
        'status': 'stopping',
        'message': 'Рассылка будет остановлена после завершения текущего письма'
    }


@outreach_router.post('/generate', response_model=GenerateLetterResponse)
async def generate_letter(request: GenerateLetterRequest):
    '''Генерация сопроводительного письма под конкретную компанию, без отправки'''
    crew = CoverLetterCrew()
    letter = await crew.generate_letter(request.company_name)
    if not letter:
        raise HTTPException(status_code=500, detail='Не удалось сгенерировать письмо')
    return GenerateLetterResponse(letter=letter)
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File

from src.core.logger import logger
from src.db.session import get_db_session
from src.db.models import User, UserResume, UserSearchFilter
from src.platforms.hh.service import search_vacancies_for_user
from src.utils.resume_loader import load_resume_text_from_bytes
from src.api.v1.schemas.hh import HHSearchResponse, UserSearchFilterUpdate
from src.db.crud import save_or_update_user_resume, save_or_update_user_filter

hh_router = APIRouter(prefix='/hh', tags=['HeadHunter'])


@hh_router.post('/user')
async def get_or_create_user(
    telegram_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    '''
    Создаёт пользователя, если не существует. Возвращает UUID.
    '''
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.exec(stmt)
    user = result.one_or_none()

    if not user:
        user = User(telegram_id=telegram_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return {'user_uuid': str(user.uuid), 'telegram_id': telegram_id}


@hh_router.post('/resume')
async def upload_resume(
    telegram_id: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session)
):
    '''
    Принимает PDF-файл резюме, парсит текст и сохраняет/обновляет.
    '''
    if file.content_type != 'application/pdf':
        raise HTTPException(status_code=400, detail='Только PDF-файлы')

    # Читаем содержимое файла
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail='Файл пуст')

    # Находим пользователя
    user_stmt = select(User).where(User.telegram_id == telegram_id)
    user_result = await session.exec(user_stmt)
    user = user_result.one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail='Пользователь не найден. Сначала вызовите /bot/user')

    # Парсим резюме из байтов
    try:
        resume_text = load_resume_text_from_bytes(contents)
    except Exception as e:
        logger.error(f'Ошибка парсинга PDF для {telegram_id}: {e}')
        raise HTTPException(status_code=400, detail='Не удалось распарсить PDF')

    # Сохраняем или обновляем
    await save_or_update_user_resume(session, user.uuid, resume_text)

    return {'status': 'success', 'message': 'Резюме успешно загружено'}


@hh_router.post('/filters')
async def set_user_filters(
    telegram_id: int,
    filters: UserSearchFilterUpdate,
    session: AsyncSession = Depends(get_db_session)
):
    '''
    Устанавливает или обновляет фильтры поиска для пользователя.
    '''
    # Находим пользователя
    user_stmt = select(User).where(User.telegram_id == telegram_id)
    user_result = await session.exec(user_stmt)
    user = user_result.one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail='Пользователь не найден. Сначала вызовите /bot/user')

    # Сохраняем/обновляем фильтры
    await save_or_update_user_filter(
        session,
        user.uuid,
        **filters.model_dump()
    )

    return {'status': 'success', 'message': 'Фильтры успешно обновлены'}


@hh_router.get('/report', response_model=HHSearchResponse)
async def get_hh_report_for_user(
    telegram_id: int,
    limit: int,
    session: AsyncSession = Depends(get_db_session)
):
    '''
    Для бота: получает свежие релевантные вакансии по настройкам пользователя.
    Не сохраняет вакансии и не помечает как "отправленные" — только просмотр.
    '''
    # 1. Найти пользователя
    user_stmt = select(User).where(User.telegram_id == telegram_id, User.is_active == True)
    user_result = await session.exec(user_stmt)
    user = user_result.one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')

    # 2. Найти резюме
    resume_stmt = select(UserResume).where(UserResume.user_uuid == user.uuid)
    resume_result = await session.exec(resume_stmt)
    resume = resume_result.one_or_none()
    if not resume:
        raise HTTPException(status_code=400, detail='Резюме не загружено')

    # 3. Найти фильтры
    filter_stmt = select(UserSearchFilter).where(UserSearchFilter.user_uuid == user.uuid)
    filter_result = await session.exec(filter_stmt)
    filter_obj = filter_result.one_or_none()
    if not filter_obj:
        raise HTTPException(status_code=400, detail='Фильтры не настроены')

    # 4. Выполнить поиск (без сохранения в SentVacancyLog)
    vacancies = await search_vacancies_for_user(
        session=session,
        user_uuid=user.uuid,
        resume_text=resume.text,
        filter_data=filter_obj.model_dump(),
        max_pages=2,
        limit_per_user=limit,
        mark_as_sent=False
    )
    return {'results': vacancies}
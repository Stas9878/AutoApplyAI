import warnings
from fastapi import FastAPI
from sqlmodel import SQLModel
from contextlib import asynccontextmanager

from src.db.session import engine
from src.core.logger import logger
from src.core.settings import settings
from src.api.v1.outreach import outreach_router
from src.db.models import ActiveContact, DeletedContact

warnings.filterwarnings(
    'ignore',
    category=UserWarning,
    message='Pydantic serializer warnings*'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Создаёт все таблицы, если их нет.
    Вызывать один раз при старте бота.
    """
    async with engine.begin() as conn:
        # Создаём все таблицы, унаследованные от SQLModel
        await conn.run_sync(SQLModel.metadata.create_all)
        logger.info('Базы созданы')

    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

app.include_router(outreach_router)


@app.get('/')
async def root():
    logger.info('Microservice is alive!')
    return {'service': 'AutoApplyAI', 'status': 'running'}


@app.get('/health')
async def health():
    return {'status': 'ok'}
import asyncio
from fastapi import FastAPI
from sqlmodel import SQLModel
from contextlib import asynccontextmanager

from src.logger import logger
from src.settings import settings
from src.db.session import get_engine
from src.db.models import ActiveContact, DeletedContact


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Создаёт все таблицы, если их нет.
    Вызывать один раз при старте бота.
    """
    async with get_engine().begin() as conn:
        # Создаём все таблицы, унаследованные от SQLModel
        await conn.run_sync(SQLModel.metadata.create_all)
        logger.info('Базы созданы')

    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)


@app.get('/')
async def root():
    logger.info('Microservice is alive!')
    return {'service': 'AutoApplyAI', 'status': 'running'}


@app.get('/health')
async def health():
    return {'status': 'ok'}
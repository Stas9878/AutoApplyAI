from fastapi import FastAPI
from sqlmodel import SQLModel
from src.db.models import ActiveContact, DeletedContact  # импортируем модели
from src.db.session import engine  # движок должен быть определён
from src.logger import logger
from src.settings import settings


# Создаём таблицы при старте (только если их нет)
SQLModel.metadata.create_all(engine)
logger.info('✅ Database tables created (if not exist)')

app = FastAPI(title=settings.app_name, debug=settings.debug)


@app.get('/')
async def root():
    logger.info('Microservice is alive!')
    return {'service': 'AutoApplyAI', 'status': 'running'}


@app.get('/health')
async def health():
    return {'status': 'ok'}
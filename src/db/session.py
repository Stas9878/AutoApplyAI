from contextlib import asynccontextmanager
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

from src.settings import settings


def get_engine(database_url: str | None = None) -> AsyncEngine:
    url = database_url or settings.database_url
    return create_async_engine(
        url,
        echo=False,
        future=True,
    )


def get_session_factory(engine: AsyncEngine):
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


# Основная фабрика (для приложения)
AsyncSessionLocal = get_session_factory(get_engine())


@asynccontextmanager
async def get_db_session():
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
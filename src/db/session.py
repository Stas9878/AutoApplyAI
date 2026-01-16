from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

from src.core.settings import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True
)


AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )


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
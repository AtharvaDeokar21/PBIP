from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


engine_options = {
    "pool_pre_ping": True,
    "pool_recycle": 1800,
    "echo": False,
}
if settings.database_url.startswith(("postgresql://", "postgresql+asyncpg://")):
    engine_options.update(pool_size=10, max_overflow=10, pool_timeout=10)

engine = create_async_engine(settings.database_url, **engine_options)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# Supabase uses PgBouncer in transaction pooling mode.
# This requires statement_cache_size=0 on the asyncpg connect_args,
# otherwise asyncpg's prepared statements conflict with PgBouncer.
# Also use NullPool when behind a connection pooler — let PgBouncer manage pooling.
from sqlalchemy.pool import NullPool

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=NullPool,          # Let PgBouncer handle pooling — don't double-pool
    connect_args={
        "statement_cache_size": 0,   # Disable asyncpg prepared statement cache
        "server_settings": {
            "application_name": "finvault",
        },
    },
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

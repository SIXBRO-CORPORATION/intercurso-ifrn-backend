import os
from dotenv import load_dotenv
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)

from sqlalchemy.pool import NullPool

from persistence.model.abstract_entity import Base
# PostgreSQL: postgresql+asyncpg://user:password@localhost:5432/dbname
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./database.db")

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async_engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit= False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as db:
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        finally:
            await db.close()

async def init_db() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drop_db() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def get_test_db() -> AsyncGenerator[AsyncSession, None]:
    from sqlalchemy.ext.asyncio import create_async_engine
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=NullPool,
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    await test_engine.dispose()

async def close_db() -> None:
    """
    Fecha todas as conexões do pool.
    Deve ser chamado no shutdown da aplicação.
    """
    await async_engine.dispose()


@asynccontextmanager
async def get_transaction():
    """
    Context manager para controle manual de transações.

    Uso:
    async with get_transaction() as session:
        # suas operações aqui
        # commit/rollback automático no final
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
# Pfad: /backend/app/database.py
"""
FlowAudit Database Configuration

Async SQLAlchemy Setup für PostgreSQL.
Verwendet asyncpg als async Treiber.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """SQLAlchemy Base-Klasse für alle Modelle."""

    pass


# Async Engine erstellen
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
)

# Async Session Factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency für FastAPI Endpoints.

    Yields:
        AsyncSession: Aktive Datenbank-Session.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context Manager für Hintergrundprozesse.

    Yields:
        AsyncSession: Aktive Datenbank-Session.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Type Alias für Dependency Injection
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]


async def init_db() -> None:
    """
    Initialisiert die Datenbank.

    Erstellt alle Tabellen falls nicht vorhanden.
    In Produktion sollte Alembic für Migrationen verwendet werden.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Schließt die Datenbankverbindung."""
    await engine.dispose()

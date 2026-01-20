# backend/app/database.py
"""
Database connection and session management using lazy initialization.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""
    pass

_engine = None
_async_session_maker = None

def get_engine():
    """Lazily initialize and return the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        logger.info("Initializing database engine.")
        # Changed from DATABASE_URL to SQLALCHEMY_DATABASE_URI
        _engine = create_async_engine(
            settings.SQLALCHEMY_DATABASE_URI,
            echo=(settings.ENVIRONMENT == "development"),  # Changed from settings.DEBUG
            future=True,
            pool_pre_ping=True
        )
    return _engine

def get_session_maker():
    """Lazily initialize and return the session maker."""
    global _async_session_maker
    if _async_session_maker is None:
        logger.info("Initializing session maker.")
        engine = get_engine()
        _async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    return _async_session_maker

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session and handles cleanup."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Aliases for backward compatibility and common conventions
SessionLocal = get_session_maker
get_db = get_async_session
get_session = get_async_session

async def create_tables() -> None:
    """Create all database tables."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

__all__ = [
    'Base',
    'get_engine',
    'SessionLocal',
    'get_async_session',
    'get_db',
    'get_session',
    'create_tables'
]
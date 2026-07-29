"""
Database connection and session management for Phase 2.2
"""

import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.pool import NullPool, QueuePool

from app.config import settings
from app.db.models import Base

logger = logging.getLogger(__name__)

# Global engine and session maker
_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker | None = None


def get_database_url() -> str:
    """
    Construct async PostgreSQL database URL.
    
    Format: postgresql+asyncpg://user:password@host:port/database
    """
    if settings.environment == "test":
        # Use in-memory SQLite for testing
        return "sqlite+aiosqlite:///:memory:"
    
    # Production/Development PostgreSQL
    return (
        f"postgresql+asyncpg://{settings.database_user}:{settings.database_password}"
        f"@{settings.database_host}:{settings.database_port}/{settings.database_name}"
    )


async def init_db():
    """
    Initialize the database engine and create tables.
    
    This should be called on application startup.
    """
    global _engine, _async_session_maker
    
    database_url = get_database_url()
    logger.info(f"Initializing database connection to {database_url.split('@')[-1] if '@' in database_url else 'in-memory'}")
    
    # Create async engine
    # Note: Don't specify poolclass for async engines - SQLAlchemy uses AsyncAdaptedQueuePool by default
    _engine = create_async_engine(
        database_url,
        echo=settings.environment == "development",  # Log SQL queries in dev
        pool_pre_ping=True,  # Verify connections before using them
        poolclass=NullPool if settings.environment == "test" else None,  # Let SQLAlchemy choose for async
        pool_size=5,  # Max 5 concurrent connections
        max_overflow=10,  # Allow up to 15 total connections
        pool_recycle=3600,  # Recycle connections after 1 hour
    )
    
    # Create session maker
    _async_session_maker = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Don't expire objects after commit
        autocommit=False,
        autoflush=False,
    )
    
    # Create all tables
    if settings.environment == "test":
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created (test mode)")
    else:
        logger.info("Database engine initialized (use Alembic for migrations)")


async def close_db():
    """
    Close the database connection.
    
    This should be called on application shutdown.
    """
    global _engine
    
    if _engine:
        await _engine.dispose()
        logger.info("Database connection closed")
        _engine = None


def get_engine() -> AsyncEngine:
    """Get the database engine."""
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _engine


def get_session_maker() -> async_sessionmaker:
    """Get the session maker."""
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _async_session_maker


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for getting a database session.
    
    Usage:
        @app.get("/users")
        async def get_users(session: AsyncSession = Depends(get_session)):
            result = await session.execute(select(User))
            return result.scalars().all()
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
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
    Context manager for getting a database session (non-FastAPI usage).
    
    Usage:
        async with get_session_context() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Health check function
async def check_db_connection() -> bool:
    """
    Check if database connection is healthy.
    
    Returns:
        True if connection is healthy, False otherwise.
    """
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False






"""
Database engine and session setup for Skippify.
Uses async SQLAlchemy with SQLite (default) or PostgreSQL.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./skippify.db")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    """FastAPI dependency that yields a database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """Create all tables on startup."""
    async with engine.begin() as conn:
        from models import Base as _  # noqa: F401 – ensure models are imported
        await conn.run_sync(Base.metadata.create_all)

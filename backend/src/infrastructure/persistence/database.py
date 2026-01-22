import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

load_dotenv()


def get_database_url() -> str:
    """Build database URL from environment variables.

    Supports both:
    - Direct DATABASE_URL
    - Separate DATABASE_HOST, DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD
    """
    # First check for direct DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # Build from separate components (used in Cloud Run)
    host = os.getenv("DATABASE_HOST", "localhost")
    name = os.getenv("DATABASE_NAME", "voicelab")
    user = os.getenv("DATABASE_USER", "postgres")
    password = os.getenv("DATABASE_PASSWORD", "postgres")
    port = os.getenv("DATABASE_PORT", "5432")

    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"


DATABASE_URL = get_database_url()

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# Alias for the dependency
get_db_session = get_db

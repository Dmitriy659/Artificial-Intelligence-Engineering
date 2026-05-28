from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.ext.asyncio.engine import create_async_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()

engine: AsyncEngine | None = None
AsyncSessionFactory: async_sessionmaker[AsyncSession] | None = None


def init_db(database_url: str) -> None:
    global engine
    global AsyncSessionFactory

    engine = create_async_engine(
        database_url,
        echo=False,
    )

    AsyncSessionFactory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )


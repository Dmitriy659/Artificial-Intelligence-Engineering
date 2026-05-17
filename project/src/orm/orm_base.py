from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from ..settings.settings import DatabaseSettings

Base = declarative_base()

engine = create_async_engine(DatabaseSettings().get_database_url_str, echo=False)

AsyncSessionFactory = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

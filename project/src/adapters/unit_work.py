import abc

from sqlalchemy.ext.asyncio import AsyncSession

from ..orm.orm_base import AsyncSessionFactory
from .repository import AbstractRepository, SqlAlchemyRepository


class AbstractUnitOfWork(abc.ABC):
    repository: AbstractRepository

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.rollback()

    @abc.abstractmethod
    async def commit(self):
        raise NotImplementedError()

    @abc.abstractmethod
    async def rollback(self):
        raise NotImplementedError()


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory=AsyncSessionFactory):
        self.session_factory = session_factory
        self.session: AsyncSession

    async def __aenter__(self):
        self.session: AsyncSession = self.session_factory()
        self.repository = SqlAlchemyRepository(self.session)
        return await super().__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()

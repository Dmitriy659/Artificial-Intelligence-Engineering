import abc
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..exceptions import ModelNotFound
from ..orm.models import AnalyticModel, ColumnModel, ORMPrediction, UserModel


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    async def get_user_by_id(self, user_id: UUID) -> UserModel:
        raise NotImplementedError()

    @abc.abstractmethod
    async def get_user_by_email(self, email: str) -> UserModel:
        raise NotImplementedError()

    @abc.abstractmethod
    async def add_user(self, user: UserModel) -> UserModel:
        raise NotImplementedError()

    @abc.abstractmethod
    async def update_user(self, user: UserModel) -> UserModel:
        raise NotImplementedError()

    @abc.abstractmethod
    async def list_analytics(self, user_id: UUID) -> list[AnalyticModel]:
        raise NotImplementedError()

    @abc.abstractmethod
    async def get_analytic_by_id(self, analytic_id: UUID, user_id: UUID | None = None) -> AnalyticModel:
        raise NotImplementedError()

    @abc.abstractmethod
    async def get_analytic_full(self, analytic_id: UUID, user_id: UUID) -> AnalyticModel:
        raise NotImplementedError()

    @abc.abstractmethod
    async def create(self, analytic: AnalyticModel) -> AnalyticModel:
        raise NotImplementedError()

    @abc.abstractmethod
    async def delete_analytic(self, analytic_id: UUID, user_id: UUID) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def update_analytic(self, analytic: AnalyticModel) -> AnalyticModel:
        raise NotImplementedError()

    @abc.abstractmethod
    async def create_columns(self, columns: list[ColumnModel]) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def add_predict(self, predict_model: ORMPrediction) -> ORMPrediction:
        raise NotImplementedError()

    @abc.abstractmethod
    async def get_predict(self, user_id: UUID, predict_id: UUID) -> ORMPrediction:
        raise NotImplementedError()

    @abc.abstractmethod
    async def get_predicts_list(self, user_id: UUID, offset: int, limit: int) -> list[ORMPrediction]:
        raise NotImplementedError()

    @abc.abstractmethod
    async def delete_predict(self, user_id: UUID, predict_id: UUID):
        raise NotImplementedError()


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_id(self, user_id: UUID) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_user(self, user: UserModel) -> UserModel:
        self.session.add(user)
        await self.session.flush()
        return user

    async def update_user(self, user: UserModel) -> UserModel:
        await self.session.flush()
        return user

    async def list_analytics(self, user_id: UUID) -> list[AnalyticModel]:
        stmt = select(AnalyticModel).where(AnalyticModel.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_analytic_by_id(self, analytic_id: UUID, user_id: UUID | None = None) -> AnalyticModel | None:
        stmt = select(AnalyticModel).where(AnalyticModel.id == analytic_id)
        if user_id is not None:
            stmt = stmt.where(AnalyticModel.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_analytic_full(self, analytic_id: UUID, user_id: UUID) -> AnalyticModel | None:
        stmt = (
            select(AnalyticModel)
            .where(AnalyticModel.id == analytic_id, AnalyticModel.user_id == user_id)
            .options(selectinload(AnalyticModel.columns))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, analytic: AnalyticModel) -> AnalyticModel:
        self.session.add(analytic)
        await self.session.flush()
        return analytic

    async def delete_analytic(self, analytic_id: UUID, user_id: UUID) -> None:
        analytic = await self.get_analytic_by_id(analytic_id, user_id)
        if not analytic:
            raise ModelNotFound()
        await self.session.delete(analytic)

    async def update_analytic(self, analytic: AnalyticModel) -> AnalyticModel:
        await self.session.flush()
        return analytic

    async def create_columns(self, columns: list[ColumnModel]) -> None:
        self.session.add_all(columns)
        await self.session.flush()

    async def add_predict(self, predict_model: ORMPrediction) -> ORMPrediction:
        self.session.add(predict_model)
        await self.session.flush()
        return predict_model

    async def get_predict(self, user_id: UUID, predict_id: UUID) -> ORMPrediction | None:
        stmt = select(ORMPrediction).where(
            ORMPrediction.id == predict_id,
            ORMPrediction.user_id == user_id,
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_predicts_list(self, user_id: UUID, offset: int, limit: int) -> list[ORMPrediction]:
        query = (
            select(ORMPrediction)
            .where(
                ORMPrediction.user_id == user_id,
            )
            .order_by(ORMPrediction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(query)
        items = result.scalars().all()

        return list(items)

    async def delete_predict(self, user_id: UUID, predict_id: UUID):
        obj: ORMPrediction | None = await self.get_predict(user_id, predict_id)
        if not obj:
            raise ModelNotFound("Predict task not found")
        await self.session.delete(obj)
        await self.session.flush()

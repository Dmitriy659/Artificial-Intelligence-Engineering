from sqlalchemy import JSON, UUID, Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .enums import AnalyticStatus, DataType, PredictionStatus
from .orm_base import Base, engine


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class UserModel(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)


class AnalyticModel(Base):
    __tablename__ = "analytic"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(Enum(AnalyticStatus, name="analytic_status"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    dataset_name = Column(String(255), nullable=False)
    dataset_s3_key = Column(String(500), nullable=False)
    analytic_result = Column(String(500), nullable=True)

    columns = relationship("ColumnModel", back_populates="analytic", cascade="all, delete-orphan")


class ColumnModel(Base):
    __tablename__ = "columns"

    id = Column(Integer, primary_key=True)
    analytic_id = Column(UUID(as_uuid=True), ForeignKey("analytic.id"), nullable=False)
    column_name = Column(String(255), nullable=False)
    data_type = Column(Enum(DataType, name="column_type"), nullable=False)
    count = Column(Integer, nullable=False)
    missing_count = Column(Integer, nullable=False)
    missing_percent = Column(Float, nullable=False)
    numeric_metrics_json = Column(JSON, nullable=True)
    string_metrics_json = Column(JSON, nullable=True)
    date_metrics_json = Column(JSON, nullable=True)

    analytic = relationship("AnalyticModel", back_populates="columns")


class ORMPrediction(Base):
    __tablename__ = "prediction"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(Enum(PredictionStatus, name="prediction_status"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    predicted_at = Column(DateTime, nullable=True)
    dataset_name = Column(String(255), nullable=False)
    report_s3_key = Column(String(255), nullable=True)
    predict_result = Column(String(1024), nullable=False, default="")

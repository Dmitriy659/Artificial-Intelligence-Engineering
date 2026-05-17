from contextlib import asynccontextmanager

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import api_router, health_router
from src.logger.configure import configure_logger
from src.logger.get_logger import get_logger
from src.orm.models import init_models

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logger()
    await init_models()
    logger.info("Models were initialized")
    os.environ["IS_READY"] = "True"
    yield
    logger.info("Exit...")


app = FastAPI(lifespan=lifespan, title="AI analyze")
app.include_router(api_router)
app.include_router(health_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # на время разработки
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

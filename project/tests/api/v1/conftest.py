import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.auth import get_current_user


def override_get_current_user():
    return {"sub": "user-123"}


@pytest.fixture
def app_factory():
    def _create_app(include_routers):
        app = FastAPI()

        for router in include_routers:
            app.include_router(router)

        app.dependency_overrides[get_current_user] = override_get_current_user
        return app

    return _create_app


@pytest.fixture
def client_factory(app_factory):
    def _create_client(routers):
        app = app_factory(routers)
        return TestClient(app)

    return _create_client

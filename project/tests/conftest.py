import pytest


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://test:test@localhost:5432/test_db",
    )

    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "8000")

    monkeypatch.setenv("SECRET_KEY", "test_secret_key")
    monkeypatch.setenv("ALGORITHM", "HS256")

    monkeypatch.setenv("AWS_KEY_ID", "test_aws_key")
    monkeypatch.setenv("AWS_SECRET_KEY", "test_aws_secret")
    monkeypatch.setenv("REGION", "eu-central-1")
    monkeypatch.setenv("S3_URL", "http://localhost:9000")
    monkeypatch.setenv("S3_BUCKET", "test-bucket")

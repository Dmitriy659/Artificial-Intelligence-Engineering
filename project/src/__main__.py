import uvicorn

from src.main import app as fastapi_app
from src.settings.settings import UvicornSettings

if __name__ == "__main__":
    uvicorn_settings = UvicornSettings()

    uvicorn.run(
        fastapi_app,
        host=uvicorn_settings.HOST,
        port=uvicorn_settings.PORT,
        proxy_headers=True,
    )

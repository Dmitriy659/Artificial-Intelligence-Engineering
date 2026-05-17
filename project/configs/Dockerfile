FROM python:3.13-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY src/ src/
COPY artifacts/catboost_final.cbm artifacts/catboost_final.cbm
COPY requirements/base.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

RUN chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["python", "-m", "src"]

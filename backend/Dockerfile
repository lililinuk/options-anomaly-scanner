FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv/nightwatch

COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic

RUN pip install --no-cache-dir .

USER 65532:65532

EXPOSE 8080

CMD ["uvicorn", "app.scheduler_main:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]

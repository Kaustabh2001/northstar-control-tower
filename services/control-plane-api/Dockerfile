FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY alembic.ini ./
COPY packages/contracts ./packages/contracts
COPY services/control-plane-api ./services/control-plane-api

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn control_plane_api.main:app --host 0.0.0.0 --port 8000"]

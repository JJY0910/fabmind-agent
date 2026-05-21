FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

COPY apps/api/pyproject.toml apps/api/uv.lock apps/api/alembic.ini ./apps/api/
COPY apps/api/app ./apps/api/app
COPY db/migrations ./db/migrations
COPY db/seeds ./db/seeds

WORKDIR /workspace/apps/api

RUN uv sync --frozen --no-cache

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

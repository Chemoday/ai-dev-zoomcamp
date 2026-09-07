# syntax=docker/dockerfile:1

FROM node:22-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


FROM python:3.12-slim AS backend
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY . .
COPY --from=frontend-build /frontend/dist ./frontend/dist
RUN uv sync --locked

ENV PATH="/app/.venv/bin:$PATH" DJANGO_SETTINGS_MODULE=config.settings

# collectstatic needs *some* SECRET_KEY present (settings.py raises if
# DEBUG=False and it's unset) but never persists it — scope it to this
# one RUN, not a persistent ENV, so it can't shadow Render's real one.
RUN SECRET_KEY=build-time-placeholder-unused DEBUG=false python manage.py collectstatic --noinput

RUN chmod +x entrypoint.sh

EXPOSE 8000
CMD ["./entrypoint.sh"]

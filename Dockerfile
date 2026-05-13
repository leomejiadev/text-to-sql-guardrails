# slim: glibc + mínimo Debian, sin build tools innecesarios.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# uv desde su imagen oficial: sin inflar la capa base con pip.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Deps primero: esta capa se reutiliza si uv.lock no cambia.
# --frozen: usa uv.lock exacto. --no-dev: sin pytest ni herramientas de dev.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .

# Instala el proyecto sobre las deps ya instaladas
RUN uv sync --frozen --no-dev

RUN chmod +x /app/docker/entrypoint.sh

EXPOSE 8000

CMD ["/app/docker/entrypoint.sh"]

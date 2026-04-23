# slim: glibc + mínimo Debian, sin build tools. Python 3.13 = pyproject.toml.
FROM python:3.13-slim

# PYTHONDONTWRITEBYTECODE: sin .pyc | PYTHONUNBUFFERED: logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# uv desde su imagen oficial: versión pineada, sin pip, sin inflar la capa.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Deps primero para aprovechar layer cache: solo se reinstalan si cambia uv.lock.
COPY pyproject.toml uv.lock ./
# --frozen: usa uv.lock exacto. --no-dev: sin pytest ni herramientas de dev.
RUN uv sync --frozen --no-dev

COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

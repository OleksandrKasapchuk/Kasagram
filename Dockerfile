# --- Stage 1: Builder ---
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Використовуємо кеш для pip, щоб не перекачувати пакети
RUN --mount=type=cache,target=/root/.cache/pip \

    pip install --upgrade pip && \

    pip install --prefix=/install -r requirements.txt

# --- Stage 2: Final Runner ---
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000

WORKDIR /app

# Встановлюємо ТІЛЬКИ runtime бібліотеки (libpq для бази)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Копіюємо встановлені пакети з першого етапу
COPY --from=builder /install /usr/local

# Копіюємо проєкт
COPY . .

# Створюємо юзера, щоб не запускати від root
RUN useradd -m myuser && \
    chown -R myuser:myuser /app

USER myuser

# Збираємо статику
RUN python manage.py collectstatic --noinput

EXPOSE 10000

CMD daphne -b 0.0.0.0 -p $PORT social_media.asgi:application
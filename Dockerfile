# Використовуємо 3.12-slim-bookworm (найсвіжіший стабільний Debian)
FROM python:3.12-slim-bookworm

# Налаштування Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Встановлюємо системні залежності
# gcc потрібен для компіляції деяких пакетів, 
# libpq-dev потрібен, якщо ти використовуєш PostgreSQL (рекомендовано для Render)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Кешування залежностей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо проєкт
COPY . .

# Збираємо статику (Render збереже її під час білду)
RUN python manage.py collectstatic --noinput

# Render ігнорує EXPOSE, але для документації залишимо змінну
ENV PORT=10000
EXPOSE 10000

# Використовуємо Daphne для ASGI
# Зверни увагу: заміни 'social_media.asgi' на шлях до твого asgi файлу
CMD daphne -b 0.0.0.0 -p $PORT social_media.asgi:application
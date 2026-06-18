# ─── Build stage ──────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─── Runtime stage ────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Копируем установленные пакеты
COPY --from=builder /install /usr/local

# Копируем код
COPY . .

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# Запуск
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

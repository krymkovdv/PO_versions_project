# Базовый образ Python 3.11
FROM python:3.11-slim

# Установка рабочей директории внутри контейнера
WORKDIR /app

# Копирование файла зависимостей
COPY requirements.txt .

# Установка системных зависимостей (libmagic1 для python-magic-bin)
# и очистка кэша для уменьшения размера образа
RUN apt-get update && apt-get install -y libmagic1 && rm -rf /var/lib/apt/lists/*

# Обновление pip и установка зависимостей Python
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копирование остальных файлов проекта в контейнер
COPY . .

# Запуск приложения через uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--proxy-headers", "--forwarded-allow-ips=*"]

# Комментарии для возможного запуска на определенном IP:
# uvicorn app.main:app --host 26.77.162.134 --port 8000
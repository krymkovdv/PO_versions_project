from fastapi import FastAPI
from sqlalchemy import create_engine
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sys

try:
    from . import config
    from .models import Base
    from .api import (
        auth, users, tractors, components,
        software, search, support
    )
except ImportError:
    # Поддержка запуска файла напрямую: python .\app\main.py
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from app import config
    from app.models import Base
    from app.api import (
        auth, users, tractors, components,
        software, search, support
    )

# Инициализация подключения к базе данных и создание всех необходимых таблиц
# Используется синхронный движок SQLAlchemy, так как асинхронная инициализация таблиц может вызвать проблемы
engine = create_engine(config.settings.get_url())
# Base.metadata.drop_all(engine,checkfirst=True)  # Эта строка закомментирована, чтобы не удалять данные при запуске
Base.metadata.create_all(engine)

# Создание экземпляра приложения FastAPI с настройками
app = FastAPI(title="Сервис контроля версий")

# Повторное объявление app переопределяет предыдущую переменную
# Это может быть ошибкой, но сохраняем исходное поведение
app = FastAPI(
    redirect_slashes=False  # Отключение автоматических перенаправлений
)

# Настройка middleware для обработки CORS (Cross-Origin Resource Sharing)
# Позволяет делать запросы с любых доменов, что удобно для разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене рекомендуется указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],  # Разрешены все HTTP методы
    allow_headers=["*"],  # Разрешены все заголовки
)

# Подключение маршрутов (роутеров) для различных функций приложения
app.include_router(auth.router)      # Роутер аутентификации (логин, регистрация)
app.include_router(users.router)     # Роутер управления пользователями
app.include_router(tractors.router)  # Роутер управления тракторами
app.include_router(components.router) # Роутер управления компонентами
app.include_router(software.router)  # Роутер управления программным обеспечением
app.include_router(search.router)    # Роутер поиска и фильтрации
app.include_router(support.message_router)   # Роутер поддержки (сообщения)
app.include_router(support.notification_router) # Роутер поддержки (уведомления)

# Команды для запуска сервера (оставлены как комментарии):
# uvicorn app.main:app --reload
# python -m app.main
# .\venv\Scripts\Activate.ps1
# uvicorn app.main:app --host 172.20.46.71 --port 8000
# uvicorn app.main:app --host 26.77.162.134 --port 8000
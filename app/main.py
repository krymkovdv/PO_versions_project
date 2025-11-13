from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from . import config
from .routes import router
from .models import Base
from fastapi.middleware.cors import CORSMiddleware


# Настройка подключения к БД
url_db = config.settings.get_url()
engine = create_engine(url_db)
SessionLocal = sessionmaker(bind=engine)

# Создание БД
# engine = create_engine(config.settings.get_url())
# Base.metadata.drop_all(engine,checkfirst=False)
# Base.metadata.create_all(engine)

#создание экземпляра приложения
app = FastAPI(title="Сервис контроля версий")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173"],  # Адрес вашего фронтенда
#     allow_credentials=True,
#     allow_methods=["*"],  # Разрешить все методы (GET, POST, PUT, DELETE, etc.)
#     allow_headers=["*"],  # Разрешить все заголовки
# )

app.include_router(router)

# uvicorn app.main:app --reload
# python -m app.main
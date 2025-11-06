from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from . import config
from .routes import router
from .models import Base

# Настройка подключения к БД
# url_db = config.settings.get_url()
# engine = create_engine(url_db)
# SessionLocal = sessionmaker(bind=engine)

#Создание БД
# engine = create_engine(config.settings.get_url())
# # Base.metadata.drop_all(engine)
# Base.metadata.create_all(engine)

#создание экземпляра приложения
app = FastAPI(title="Сервис контроля версий")

app.include_router(router)

# uvicorn app.main:app --reload
# python -m app.main
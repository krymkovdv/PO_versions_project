from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import models, config
from .routes import router


#Создание БД
# engine = create_engine(config.settings.get_url())
# Base.metadata.drop_all(engine)
# Base.metadata.create_all(engine)

#создание экземпляра приложения
app = FastAPI(title="Сервис контроля версий")

app.include_router(router)

# uvicorn app.main:app --reload
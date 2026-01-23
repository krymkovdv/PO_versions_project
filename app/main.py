from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from . import config
from .routes import router
from .models import Base
from fastapi.middleware.cors import CORSMiddleware





# Создание БД
engine = create_engine(config.settings.get_url())
# Base.metadata.drop_all(engine,checkfirst=True)
Base.metadata.create_all(engine)

#создание экземпляра приложения
app = FastAPI(title="Сервис контроля версий")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"]
)

app.include_router(router)

# uvicorn app.main:app --reload
# python -m app.main
# .\venv\Scripts\Activate.ps1
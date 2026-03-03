from fastapi import FastAPI
from sqlalchemy import create_engine
from . import config
from .models import Base
from fastapi.middleware.cors import CORSMiddleware

from .api import (
    auth, users, tractors, components, 
    software, search
)



# Создание БД
engine = create_engine(config.settings.get_url())
# Base.metadata.drop_all(engine,checkfirst=True)
Base.metadata.create_all(engine)

#создание экземпляра приложения
app = FastAPI(title="Сервис контроля версий")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"]
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tractors.router)
app.include_router(components.router)
app.include_router(software.router)
app.include_router(search.router)

# uvicorn app.main:app --reload
# python -m app.main
# .\venv\Scripts\Activate.ps1
# uvicorn app.main:app --host 172.20.46.71 --port 8000
# uvicorn app.main:app --host 26.77.162.134 --port 8000
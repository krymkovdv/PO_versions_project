from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from . import config
from .routes import router
from .models import Base
from fastapi.middleware.cors import CORSMiddleware
from .log import logger
import logging




# Создание БД
# engine = create_engine(config.settings.get_url())
# # Base.metadata.drop_all(engine,checkfirst=False)
# Base.metadata.create_all(engine)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
#создание экземпляра приложения
app = FastAPI(title="Сервис контроля версий")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Адрес вашего фронтенда
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Разрешить все заголовки
)

# @app.middleware("http")
# async def log_requests(request, call_next):
#     logger.info(f"📥 {request.method} {request.url} — от {request.client.host}")
#     response = await call_next(request)
#     logger.info(f"📤 {request.method} {request.url} — статус: {response.status_code}")
#     return response



app.include_router(router)

# uvicorn app.main:app --reload
# python -m app.main
# .\venv\Scripts\Activate.ps1
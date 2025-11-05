from sqlalchemy import create_engine,select
import psycopg2
from fastapi import FastAPI,Depends
import app.config as config
from app.models import Base, Tractors,TractorComponent
from sqlalchemy.orm import sessionmaker, Session
from app.routes import *
from fastapi.middleware.cors import CORSMiddleware



url_db = config.settings.get_url()
engine = create_engine(url_db)


SessionLocal = sessionmaker(bind=engine)

def get_session():
    with SessionLocal() as session:
        yield session





# with Session() as session:
#     with session.begin():
#         trac1 = Tractors(model ='743', region ='c1', owner_name = 'Vanya')
#         session.add(trac1)



Base.metadata.create_all(engine)
#создание экземпляра приложения
app = FastAPI(title="Сервис контроля версий")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500"],  # Адрес вашего React dev сервера
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы (GET, POST, etc.)
    allow_headers=["*"],  # Разрешить все заголовки
)

app.include_router(router)

# uvicorn main:app
# .\venv\Scripts\Activate.ps1

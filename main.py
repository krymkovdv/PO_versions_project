from sqlalchemy import create_engine
from fastapi import FastAPI


SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
 
# создание движка
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

#создание экземпляра приложения
app = FastAPI(title="Сервис контроля версий")
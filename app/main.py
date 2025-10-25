from sqlalchemy import create_engine, select
from fastapi import FastAPI, Depends
import config as config
from models import *
from sqlalchemy.orm import sessionmaker, Session
import psycopg2
from app.routes import *



# with Session() as session:
#     with session.begin():
#         trac1 = Tractors(model ='743', region ='c1', owner_name = 'Vanya')
#         session.add(trac1)

#Создание БД
# Base.metadata.drop_all(engine)
# Base.metadata.create_all(engine)

#создание экземпляра приложения
app = FastAPI(title="Сервис контроля версий")

app.include_router(router)

# uvicorn app.main:app --reload
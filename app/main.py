from sqlalchemy import create_engine,select
import psycopg2
from fastapi import FastAPI,Depends
import app.config as config
from app.models import Base, Tractors,TractorComponent
from sqlalchemy.orm import sessionmaker, Session
from app.routes import *







# with Session() as session:
#     with session.begin():
#         trac1 = Tractors(model ='743', region ='c1', owner_name = 'Vanya')
#         session.add(trac1)



# Base.metadata.create_all(engine)
#создание экземпляра приложения
app = FastAPI(title="Сервис контроля версий")

app.include_router(router)

# uvicorn main:app
# .\venv\Scripts\Activate.ps1
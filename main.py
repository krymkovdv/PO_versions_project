from sqlalchemy import create_engine
import psycopg2
from fastapi import FastAPI
import config
from models import Base, Tractors,TractorComponent
from sqlalchemy.orm import sessionmaker

url_db = config.settings.get_url()

 
# создание движка
engine = create_engine(
    url_db,
)

Session = sessionmaker(bind=engine)

with Session() as session:
    with session.begin():
        trac1 = Tractors(model ='743', region ='c1', owner_name = 'Vanya')
        session.add(trac1)
        

# Base.metadata.create_all(engine)
#создание экземпляра приложения
app = FastAPI(title="Сервис контроля версий")
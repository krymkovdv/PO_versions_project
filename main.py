from sqlalchemy import create_engine,select
import psycopg2
from fastapi import FastAPI,Depends
import config
from models import Base, Tractors,TractorComponent
from sqlalchemy.orm import sessionmaker, Session
from schemas import TractorsSchema

url_db = config.settings.get_url()

 
# создание движка
engine = create_engine(
    url_db,
)




SessionLocal = sessionmaker(bind=engine)


# 2. Функция зависимости — ОБЯЗАТЕЛЬНО до эндпоинтов!
def get_session():
    with SessionLocal() as session:
        yield session


# with Session() as session:
#     with session.begin():
#         trac1 = Tractors(model ='743', region ='c1', owner_name = 'Vanya')
#         session.add(trac1)



# Base.metadata.create_all(engine)
#создание экземпляра приложения
app = FastAPI(title="Сервис контроля версий")


@app.get("/tractors/", response_model=list[TractorsSchema])
def get_tractors(session: Session = Depends(get_session)):
    tractors = session.execute(select(Tractors)).scalars().all()
    return tractors  # FastAPI автоматически сериализует через Pydantic

# uvicorn main:app
# .\venv\Scripts\Activate.ps1
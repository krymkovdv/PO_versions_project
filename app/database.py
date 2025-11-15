from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import settings

url_db = settings.get_url()
engine = create_engine(url_db)
SessionLocal = sessionmaker(bind=engine)

def get_session():
    with SessionLocal() as session:
        yield session

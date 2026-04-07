from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import settings

# Получение URL базы данных из конфигурации
url_db = settings.get_url()

# Создание движка SQLAlchemy с полученным URL
engine = create_engine(url_db)

# Создание локального сеанса базы данных
SessionLocal = sessionmaker(bind=engine)

def get_session():
    """
    Генератор сеанса базы данных для использования в зависимостях FastAPI
    
    Yields:
        Сеанс базы данных SQLAlchemy
    """
    with SessionLocal() as session:
        yield session
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError  # ← для перехвата ошибок БД
from app.schemas import TractorsSchema, FirmwareInfo, ComponentInfo
from app.models import Tractors, Firmwares, TelemetryComponents
import app.config as config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

router = APIRouter()

# Настройка подключения к БД (лучше вынести в отдельный файл, но оставим пока здесь)
url_db = config.settings.get_url()
engine = create_engine(url_db)
SessionLocal = sessionmaker(bind=engine)

def get_session():
    with SessionLocal() as session:
        yield session


@router.get("/tractors/", response_model=list[TractorsSchema])
def get_tractors(session: Session = Depends(get_session)):
    try:
        stmt = select(Tractors)
        result = session.execute(stmt).scalars().all()
        return result
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении тракторов: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )


@router.get("/firmwares/", response_model=list[FirmwareInfo])
def get_firmwares(session: Session = Depends(get_session)):
    try:
        stmt = select(Firmwares)
        result = session.execute(stmt).scalars().all()
        return result
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении прошивок: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )


@router.get("/components/", response_model=list[ComponentInfo])
def get_components(session: Session = Depends(get_session)): 
    try:
        stmt = select(TelemetryComponents)
        result = session.execute(stmt).scalars().all()
        return result
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении компонентов: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )
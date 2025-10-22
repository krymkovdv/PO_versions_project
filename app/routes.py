from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError  # ← для перехвата ошибок БД
from app.schemas import TractorsSchema, FirmwareInfo, ComponentInfo
from app.models import Tractors, Firmwares, TelemetryComponents
import app.config as config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import CRUDs, schemas
from typing import List


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
    







# Эндпоинт 1: Получить список ПО по фильтрам
@router.post("/tractors/software", response_model=List[schemas.TractorSoftwareResponse])
def get_tractor_software(filters: schemas.TractorFilter, db: Session = Depends(get_session)):
    try:
        software_list = CRUDs.get_tractor_software(db, filters)
        return software_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Эндпоинт 2: Скачать прошивку
@router.get("/firmware/download/{firmware_id}")
def download_firmware(firmware_id: int, db: Session = Depends(get_session)):
    fw = CRUDs.download_firmware(db, firmware_id)
    if not fw:
        raise HTTPException(status_code=404, detail="Firmware not found")
    
    # В реальности здесь должен быть редирект или отправка файла
    # Например:
    # return FileResponse(path=fw.download_link, filename=f"{fw.producer_version}.bin")
    
    # Для теста — возвращаем JSON с ссылкой
    return {"download_url": fw.download_link, "filename": f"{fw.producer_version}.bin"}


# Эндпоинт 3: Умный поиск
@router.post("/tractors/search")
def search_tractors(query: str, db: Session = Depends(get_session)):
    tractors = CRUDs.smart_search_tractors(db, query)
    return [{"terminal_id": t.terminal_id, "model": t.model, "region": t.region} for t in tractors]
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import crud, schemas, database

router = APIRouter()

# Зависимость для сессии
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Эндпоинт 1: Получить список ПО по фильтрам
@router.post("/tractors/software", response_model=List[schemas.TractorSoftwareResponse])
def get_tractor_software(filters: schemas.TractorFilter, db: Session = Depends(get_db)):
    try:
        software_list = crud.get_tractor_software(db, filters)
        return software_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Эндпоинт 2: Скачать прошивку
@router.get("/firmware/download/{firmware_id}")
def download_firmware(firmware_id: int, db: Session = Depends(get_db)):
    fw = crud.download_firmware(db, firmware_id)
    if not fw:
        raise HTTPException(status_code=404, detail="Firmware not found")
    
    # В реальности здесь должен быть редирект или отправка файла
    # Например:
    # return FileResponse(path=fw.download_link, filename=f"{fw.producer_version}.bin")
    
    # Для теста — возвращаем JSON с ссылкой
    return {"download_url": fw.download_link, "filename": f"{fw.producer_version}.bin"}


# Эндпоинт 3: Умный поиск
@router.post("/tractors/search")
def search_tractors(query: str, db: Session = Depends(get_db)):
    tractors = crud.smart_search_tractors(db, query)
    return [{"terminal_id": t.terminal_id, "model": t.model, "region": t.region} for t in tractors]
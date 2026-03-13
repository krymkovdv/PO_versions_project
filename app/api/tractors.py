from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from sqlalchemy.orm import Session

from .. import schemas, crud, models
from ..database import get_session
from ..authorization import require_role, get_current_user
from ..log import logger
from typing import List
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(prefix="/tractors", tags=["Tractors"])

@router.get("/", response_model=list[schemas.TractorsSchema])
def get_tractors(db: Session = Depends(get_session), current_user: models.UserDB = Depends(get_current_user)):
    logger.info(f"[get_tractors] Получение списка тракторов user={current_user.username} role={current_user.role}")
    try: 
        tractors = crud.tractors.get_tractors(db)
        logger.info(f"[get_tractor] запрос успешно выполнен user={current_user.username} role={current_user.role}")
        return tractors
    except SQLAlchemyError as e:
        logger.error(f"[get_tractors] Ошибка SQLAlchemy: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении тракторов: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[get_tractors] неизвестная ошибка: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )

@router.post("", response_model=schemas.TractorsSchema, status_code=status.HTTP_201_CREATED,dependencies=[Depends(require_role("moderator"))])
def create_tractor(tractor: schemas.TractorsSchema, db: Session = Depends(get_session), current_user: models.UserDB = Depends(get_current_user)):
    # Проверка на дубликат vin (если нужно)
    existing = db.query(models.Tractors).filter(models.Tractors.vin == tractor.vin).first()
    if existing:
        logger.error(f"Трактор с vin: {tractor.vin} уже есть user={current_user.username} role={current_user.role}")
        raise HTTPException(status_code=400, detail="Tractor with this VIN already exists")
    try:
        created_tractor = crud.tractors.create_tractor(db, tractor)
        logger.info(f"Трактор с vin: {tractor.vin} создан user={current_user.username} role={current_user.role}")
        return created_tractor
    except SQLAlchemyError as e:
        logger.error(f"[create_tractor] ошибка SQLAlchemy: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при создании трактора: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[create_tractor] неизвестная ошибка: {str(e)} user={current_user.username} role={current_user.role}",  exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )

@router.delete("/{tractor_id}", status_code=status.HTTP_204_NO_CONTENT,dependencies=[Depends(require_role("moderator"))])
def delete_tractor(tractor_id: int, db: Session = Depends(get_session), current_user: models.UserDB = Depends(get_current_user)):
    try:
        success = crud.tractors.delete_tractor(db, tractor_id)
        if not success:
            logger.warning(f"[delete_tractor] трактор с id {tractor_id} не найден user={current_user.username} role={current_user.role}")
            raise HTTPException(status_code=404, detail="Tractor not found")
        logger.info(f"[delete_tractor] успешно удалён трактор с id {tractor_id} user={current_user.username} role={current_user.role}")
    except Exception as e:
        logger.error(f"[delete_tractor] ошибка: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )

@router.patch("/{vin}", response_model=schemas.TractorsSchema)
def update_tractor(
    vin: str,
    tractor_update: schemas.TractorUpdate,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    if current_user.role not in ["moderator"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return crud.tractors.update_tractor(db, vin, tractor_update)
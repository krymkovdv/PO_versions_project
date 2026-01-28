from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from sqlalchemy.orm import Session

from .. import schemas, crud, models
from ..database import get_session
from ..authorization import require_role, get_current_user
from ..log import logger
from typing import List
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(prefix="/telemetry-components", tags=["Telemetry-components"])

@router.get("/", response_model=list[schemas.TelemetryComponentSchema])
def get_telemetry_components(session: Session = Depends(get_session)):
    try:
        logger.info(f"[get_telemetryComponents] запрос выполнен user=anonymous role=anonymous")
        return crud.telemetry.get_telemetry_components(session)
    except SQLAlchemyError as e:
        logger.error(f"[get_telemetryComponents] Ошибка SQLAlchemy: {str(e)} user=anonymous role=anonymous",  exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении телеметрии: {str(e)}" 
        )
    except Exception as e:
        logger.error(f"[get_telemetryComponents] неизвестная ошибка: {str(e)} user=anonymous role=anonymous",  exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )
    
@router.post("/telemetry-components/", response_model=schemas.TelemetryComponentSchema, status_code=status.HTTP_201_CREATED,dependencies=[Depends(require_role("moderator"))])
def create_telemetry_component(telemetry_component: schemas.TelemetryComponentSchema, db: Session = Depends(get_session), current_user: models.UserDB = Depends(get_current_user)):
    # Проверка на дубликат comp_ser_num
    if telemetry_component.comp_ser_num:
        existing = db.query(models.TelemetryComponents).filter(models.TelemetryComponents.comp_ser_num == telemetry_component.comp_ser_num).first()
        if existing:
            logger.error(f"Телеметрия с серийным номером {telemetry_component.comp_ser_num} уже существует user={current_user.username} role={current_user.role}")
            raise HTTPException(status_code=400, detail="Telemetry with this serial number already exists")
    try:
        result = crud.telemetry.create_telemetry_component(db, telemetry_component)
        logger.info(f"[post_telemetry-component] успешно выполнена user={current_user.username} role={current_user.role}")
        return result
    except SQLAlchemyError as e:
        logger.error(f"[post_telemetry-component] ошибка SQLAlchemy: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при создании телеметрии: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[post_telemetry-component] неизвестная ошибка: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )

@router.delete("/telemetry-components/{telemetry_id}", status_code=status.HTTP_204_NO_CONTENT,dependencies=[Depends(require_role("moderator"))])
def delete_telemetry_component(telemetry_id: int, db: Session = Depends(get_session), current_user: models.UserDB = Depends(get_current_user)):
    success = crud.telemetry.delete_telemetry_component(db, telemetry_id)
    if not success:
        logger.error(f"[delete_telemetry_component] телеметрия {telemetry_id} не найдена user={current_user.username} role={current_user.role}")
        raise HTTPException(status_code=404, detail="Telemetry not found")
    logger.info(f"[delete_telemetry_component] телеметрия {telemetry_id} удалена user={current_user.username} role={current_user.role}")

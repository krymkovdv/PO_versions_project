from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from sqlalchemy.orm import Session

from .. import schemas, crud, models
from ..database import get_session
from ..authorization import require_role, get_current_user
from ..log import logger
from typing import List
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(prefix="/components", tags=["Components"])

@router.get("/", response_model=list[schemas.ComponentSchema])
def get_component(
    session: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    try:
        logger.info(f"[get_component] запрос успешно выполнен user={current_user.username} role={current_user.role}")
        return crud.components.get_components(session)
    except SQLAlchemyError as e:
        logger.error(f"[get_component] Ошибка SQLAlchemy: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении компонентов тракторов: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[get_components] неизвестная ошибка: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )

@router.post("/", response_model=schemas.ComponentSchema, status_code=status.HTTP_201_CREATED,dependencies=[Depends(require_role("moderator"))])
def create_component(component: schemas.ComponentSchema, db: Session = Depends(get_session), current_user: models.UserDB = Depends(get_current_user)):
    try:
        # Проверка на дубликат terminal_id
        if crud.components.get_component_by_id(db, component.id):
            logger.error(f"Компонент с id: {component.id} уже существует user={current_user.username} role={current_user.role}")
            raise HTTPException(status_code=400, detail="Tractor component with this terminal_id already exists user={current_user.username} role={current_user.role}")
        result = crud.components.create_component(db, component)
        logger.info(f"Компонент с id: {component.id} создан user={current_user.username} role={current_user.role}")
        return result
    except Exception as e:
        logger.error(f"[create_component] ошибка: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{row_id}", status_code=status.HTTP_204_NO_CONTENT,dependencies=[Depends(require_role("moderator"))])
def delete_component(id: int, db: Session = Depends(get_session), current_user: models.UserDB = Depends(get_current_user)):
    success = crud.components.delete_component(db, id)
    if not success:
        logger.error(f"[delete_component] неизвестная ошибка user={current_user.username} role={current_user.role}")
        raise HTTPException(status_code=404, detail="Tractor component not found")
    logger.info(f"[delete_component] компонент {id} удалён user={current_user.username} role={current_user.role}")

@router.get("/component-parts/", response_model=List[schemas.ComponentPartSchema])
def get_components_parts(session: Session = Depends(get_session)): 
    try:
        logger.info(f"[get_component-parts] успешно выполнена user=anonymous role=anonymous")
        return crud.components.get_component_parts(session)
    except SQLAlchemyError as e:
        logger.error(f"[get_component-parts] ошибка SQLAlchemy: {str(e)} user=anonymous role=anonymous", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении компонентов частей: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[get_component-parts] неизвестная ошибка: {str(e)} user=anonymous role=anonymous", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )
    
@router.post("/component-parts/", response_model=schemas.ComponentPartSchema, status_code=status.HTTP_201_CREATED,dependencies=[Depends(require_role("moderator"))])
def create_component_parts(part: schemas.ComponentPartSchema, db: Session = Depends(get_session), current_user: models.UserDB = Depends(get_current_user)):
    # Проверка на дубликат part_type + component (если нужно)
    existing = db.query(models.ComponentParts).filter(
        models.ComponentParts.component == part.component,
        models.ComponentParts.part_type == part.part_type  # <--- part_type
    ).first()
    if existing:
        logger.error(f"Часть компонента уже существует: {part.component}/{part.part_number} user={current_user.username} role={current_user.role}")
        raise HTTPException(status_code=400, detail="Component part with this type already exists for this component")
    try:
        result = crud.components.create_component_part(db, part)
        logger.info(f"[post_component-parts] успешно выполнена user={current_user.username} role={current_user.role}")
        return result
    except SQLAlchemyError as e:
        logger.error(f"[post_component-parts] ошибка SQLAlchemy: {str(e)} user={current_user.username} role={current_user.role}",  exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при создании части компонента: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[post_component-parts] неизвестная ошибка: {str(e)} user={current_user.username} role={current_user.role}",  exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )

@router.delete("/component-parts/{part_id}", status_code=status.HTTP_204_NO_CONTENT,dependencies=[Depends(require_role("moderator"))])
def delete_component_part(part_id: int, db: Session = Depends(get_session), current_user: models.UserDB = Depends(get_current_user)):
    success = crud.components.delete_component_part(db, part_id)
    if not success:
        logger.error(f"[delete_component_part] часть {part_id} не найдена user={current_user.username} role={current_user.role}")
        raise HTTPException(status_code=404, detail="Component part not found")
    logger.info(f"[delete_component_part] часть {part_id} удалена user={current_user.username} role={current_user.role}")

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from sqlalchemy.orm import Session

from .. import schemas, crud, models
from ..database import get_session
from ..authorization import require_role, get_current_user
from ..log import logger
from sqlalchemy.exc import SQLAlchemyError

# Создание маршрутизатора для компонентов трактора
router = APIRouter(prefix="/components", tags=["Components"])

@router.get("", response_model=list[schemas.ComponentSchema])
def get_component(
    session: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """
    Получение списка всех компонентов трактора
    
    Args:
        session: Сессия базы данных
        current_user: Текущий аутентифицированный пользователь
    
    Returns:
        Список компонентов
    """
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

@router.post("", response_model=schemas.ComponentSchema, status_code=status.HTTP_201_CREATED,dependencies=[Depends(require_role("moderator"))])
def create_component(component: schemas.ComponentSchema, db: Session = Depends(get_session), current_user: models.UserDB = Depends(get_current_user)):
    """
    Создание нового компонента трактора
    Доступно только для модераторов
    
    Args:
        component: Данные компонента для создания
        db: Сессия базы данных
        current_user: Текущий аутентифицированный пользователь
    
    Returns:
        Созданный компонент
    """
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
    """
    Удаление компонента по ID
    Доступно только для модераторов
    
    Args:
        id: ID компонента для удаления
        db: Сессия базы данных
        current_user: Текущий аутентифицированный пользователь
    """
    success = crud.components.delete_component(db, id)
    if not success:
        logger.error(f"[delete_component] неизвестная ошибка user={current_user.username} role={current_user.role}")
        raise HTTPException(status_code=404, detail="Tractor component not found")
    logger.info(f"[delete_component] компонент {id} удалён user={current_user.username} role={current_user.role}")

@router.patch("/{component_id}", response_model=schemas.ComponentSchema)
def update_component(
    component_id: int,
    component_update: schemas.ComponentUpdate,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """
    Обновление информации о компоненте
    Доступно только для модераторов
    
    Args:
        component_id: ID компонента для обновления
        component_update: Данные для обновления
        db: Сессия базы данных
        current_user: Текущий аутентифицированный пользователь
    
    Returns:
        Обновленный компонент
    """
    if current_user.role != "moderator":
        raise HTTPException(status_code=403, detail="Only moderator can update components")
    return crud.components.update_component(db, component_id, component_update)
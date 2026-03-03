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

@router.post("/", response_model=schemas.TractorsSchema, status_code=status.HTTP_201_CREATED,dependencies=[Depends(require_role("moderator"))])
def create_tractor(tractor: schemas.TractorsSchema, db: Session = Depends(get_session), current_user: models.UserDB = Depends(get_current_user)):
    # Проверка на дубликат vin (если нужно)
    existing = db.query(models.Tractor).filter(models.Tractor.vin == tractor.vin).first()
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

# ============================================
# Эндпоинты для связи Трактор ↔ ПО ↔ Компонент
# ============================================

@router.get("/{tractor_id}/software-components", response_model=List[schemas.TractorSoftwareComponentLinkSchema])
def get_tractor_software_components(
    tractor_id: int,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Получить все связи ПО-Компонент для трактора"""
    try:
        links = crud.tractor_software_component_link.get_links_by_tractor_id(db, tractor_id)
        logger.info(
            f"[get_tractor_software_components] найдено связей: {len(links)} "
            f"tractor_id={tractor_id} user={current_user.username} role={current_user.role}"
        )
        return links
    except Exception as e:
        logger.error(f"[get_tractor_software_components] ошибка: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении связей: {str(e)}"
        )

@router.get("/{tractor_id}/software-components/details", response_model=List[schemas.TractorSoftwareResponse])
def get_tractor_software_components_details(
    tractor_id: int,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Получить связи с подробной информацией о тракторе, ПО и компоненте"""
    try:
        details = crud.tractor_software_component_link.get_tractor_software_with_details(db, tractor_id)
        logger.info(
            f"[get_tractor_software_components_details] найдено записей: {len(details)} "
            f"tractor_id={tractor_id} user={current_user.username}"
        )
        return details
    except Exception as e:
        logger.error(f"[get_tractor_software_components_details] ошибка: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении деталей: {str(e)}"
        )

@router.get("/vin/{vin}/software-components", response_model=List[schemas.TractorSoftwareResponse])
def get_tractor_software_components_by_vin(
    vin: str,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Получить связи ПО-Компонент для трактора по VIN"""
    try:
        details = crud.tractor_software_component_link.get_tractor_software_with_details_by_vin(db, vin)
        logger.info(
            f"[get_tractor_software_components_by_vin] найдено записей: {len(details)} "
            f"vin={vin} user={current_user.username}"
        )
        return details
    except Exception as e:
        logger.error(f"[get_tractor_software_components_by_vin] ошибка: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении деталей: {str(e)}"
        )

@router.post("/{tractor_id}/software-components", status_code=201)
def link_software_component_to_tractor(
    tractor_id: int,
    link: schemas.TractorSoftwareComponentLinkCreate,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Связать ПО-Компонент с трактором"""
    
    # Проверка прав (только engineer или moderator)
    if current_user.role not in ['engineer', 'moderator']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only engineers or moderators can link software to tractors"
        )
    
    # Принудительно устанавливаем tractor_id из URL
    link.tractor_id = tractor_id
    
    try:
        db_link = crud.tractor_software_component_link.create_tractor_software_component_link(db, link)
        logger.info(
            f"[link_software_component_to_tractor] создана связь "
            f"tractor_id={tractor_id}, soft_comp_link_id={link.soft_comp_link_id} "
            f"user={current_user.username} role={current_user.role}"
        )
        return {
            "id": db_link.id,
            "tractor_id": db_link.tractor_id,
            "soft_comp_link_id": db_link.soft_comp_link_id,
            "is_recom": db_link.is_recom
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"[link_software_component_to_tractor] ошибка: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании связи: {str(e)}"
        )

@router.put("/{tractor_id}/software-components/{link_id}")
def update_tractor_software_component_link(
    tractor_id: int,
    link_id: int,
    link_update: schemas.TractorSoftwareComponentLinkUpdate,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Обновить связь ПО-Компонент с трактором"""
    
    # Проверка прав
    if current_user.role not in ['engineer', 'moderator']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only engineers or moderators can update tractor software links"
        )
    
    # Проверка что связь принадлежит трактору
    db_link = crud.tractor_software_component_link.get_tractor_software_component_link_by_id(db, link_id)
    if not db_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    if db_link.tractor_id != tractor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Link does not belong to this tractor"
        )
    
    try:
        updated_link = crud.tractor_software_component_link.update_tractor_software_component_link(
            db, link_id, link_update
        )
        logger.info(
            f"[update_tractor_software_component_link] обновлена связь link_id={link_id} "
            f"user={current_user.username} role={current_user.role}"
        )
        return {
            "id": updated_link.id,
            "is_recom": updated_link.is_recom,
            "mounted_date": updated_link.mounted_date
        }
    except Exception as e:
        logger.error(f"[update_tractor_software_component_link] ошибка: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении связи: {str(e)}"
        )

@router.delete("/{tractor_id}/software-components/{link_id}", status_code=204)
def delete_tractor_software_component_link(
    tractor_id: int,
    link_id: int,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Удалить связь ПО-Компонент с трактором"""
    
    # Проверка прав
    if current_user.role not in ['engineer', 'moderator']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only engineers or moderators can delete tractor software links"
        )
    
    # Проверка что связь принадлежит трактору
    db_link = crud.tractor_software_component_link.get_tractor_software_component_link_by_id(db, link_id)
    if not db_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    if db_link.tractor_id != tractor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Link does not belong to this tractor"
        )
    
    try:
        crud.tractor_software_component_link.delete_tractor_software_component_link(db, link_id)
        logger.info(
            f"[delete_tractor_software_component_link] удалена связь link_id={link_id} "
            f"user={current_user.username} role={current_user.role}"
        )
        return None
    except Exception as e:
        logger.error(f"[delete_tractor_software_component_link] ошибка: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении связи: {str(e)}"
        )

@router.delete("/{tractor_id}/software-components", status_code=204)
def delete_all_tractor_software_component_links(
    tractor_id: int,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Удалить все связи ПО-Компонент для трактора"""
    
    # Проверка прав (только moderator)
    if current_user.role != 'moderator':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only moderators can delete all tractor software links"
        )
    
    try:
        count = crud.tractor_software_component_link.delete_all_links_by_tractor_id(db, tractor_id)
        logger.info(
            f"[delete_all_tractor_software_component_links] удалено связей: {count} "
            f"tractor_id={tractor_id} user={current_user.username} role={current_user.role}"
        )
        return None
    except Exception as e:
        logger.error(f"[delete_all_tractor_software_component_links] ошибка: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении связей: {str(e)}"
        )
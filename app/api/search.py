from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from sqlalchemy.orm import Session

from .. import schemas, crud, models
from ..database import get_session
from ..authorization import require_role, get_password_hash, get_current_user
from ..log import logger
from typing import List
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(prefix="/search", tags=["Search"])

#Страница с агрегатами
@router.post("/component-info", response_model=List[schemas.ComponentSearchResponseItem])
def get_component_by_filters(
    filters: schemas.ComponentInfoRequest,
    current_user: models.UserDB = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    logger.info(f"[component-info] запрос filters={filters.dict()} user={current_user.username} role={current_user.role}")
    try:
        response = crud.search.get_component_by_filters(
            db,
            trac_model=filters.trac_model,
            type_comp=filters.type_comp,
            name_comp=filters.name_comp,
            producers=filters.producers,
            status=filters.status
        )
        logger.info(f"[component-info] успешно выполнена, найдено записей: {len(response)} user={current_user.username} role={current_user.role}")
        return response
    except Exception as e:
        logger.error(f"[component-info] ошибка: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-component", response_model=List[schemas.ComponentSearchResponseItem])
def get_search_component(
    query: str,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    logger.info(f"[search-component] запрос={query} user={current_user.username} role={current_user.role}")
    try:
        return crud.search.search_components(db, model_comp=query)
    except ValueError as ve:
        logger.error(f"[search-component] ошибка: {str(ve)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"[search-component] неизвестная ошибка: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/software-component-info", response_model=List[schemas.SoftwareComponentInfoResponse])
def get_software_component_by_ids(
    id_firmwares: int,
    id_component: int,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """
    Получение полной информации о ПО и компоненте по их ID.
    
    - **id_firmwares**: ID программного обеспечения (Software.id)
    - **id_component**: ID компонента (Component.id)
    
    Возвращает полную информацию о ПО, компоненте и их связи.
    """
    logger.info(f"[software-component-info] запрос id_firmwares={id_firmwares} id_component={id_component} user={current_user.username} role={current_user.role}")
    
    try:
        response = crud.search.get_software_component_by_ids(
            db,
            id_firmwares=id_firmwares,
            id_component=id_component
        )
        
        if not response:
            logger.warning(f"[software-component-info] не найдено id_firmwares={id_firmwares} id_component={id_component} user={current_user.username}")
            raise HTTPException(
                status_code=404,
                detail=f"Software {id_firmwares} и Component {id_component} не найдены или не связаны"
            )
        
        logger.info(f"[software-component-info] успешно найдено записей: {len(response)} user={current_user.username}")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[software-component-info] ошибка: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# --- Страница 4: Поиск тракторов ---
@router.post("/tractor-info", response_model=List[schemas.TractorSearchResponse])
def get_tractors_by_filters(
    filters: schemas.TractorFilter, 
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    logger.info(f"[tractor-info] фильтры={filters.dict()} user={current_user.username} role={current_user.role}")
    try:
        data = crud.search.get_tractors_by_filters(db, filters)
        logger.info(f"[tractor-info] найдено записей: {len(data)} user={current_user.username} role={current_user.role}")
        return data
    except Exception as e:
        logger.error(f"[tractor-info] ошибка: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tractor-components", response_model=List[schemas.TractorComponentResponse])
def get_tractor_components(
    request: schemas.TractorComponentRequest,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    logger.info(f"[tractor-components] запрос VIN={request.vins} user={current_user.username} role={current_user.role}")
    
    try:
        response_data = crud.search.get_tractor_components_by_vin(db, request)
        logger.info(f"[tractor-components] найдено записей: {len(response_data)} user={current_user.username}")
        return response_data
    except Exception as e:
        logger.error(f"[tractor-components] ошибка: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при получении компонентов: {str(e)}")

@router.get("/search-tractor-vin", response_model=List[schemas.TractorSearchResponse2])
def get_search_tractors_vin(
    request: str, 
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    logger.info(f"[search-tractor-vin] запрос={request} user={current_user.username} role={current_user.role}")
    try:
        return crud.search.get_tractor_by_vin(db, vin=request)
    except Exception as e:
        logger.error(f"[search-tractor-vin] ошибка: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# @router.post("/component-models")
# def get_component_models(
#     request: schemas.RequestModel,
#     db: Session = Depends(get_session),
#     current_user: models.UserDB = Depends(get_current_user)
# ):
#     logger.info(f"[component-models] запрос={request.dict()} user={current_user.username} role={current_user.role}")
#     try:
#         models_list = crud.components.get_agg_by_trac_and_comp(
#             db,
#             trac_model=request.trac_model if request.trac_model else None,
#             type_comp=request.type_comp if request.type_comp else None,
#             producers=request.producers if request.producers else None,
#             status=request.status if request.status else None
#         )
#         logger.info(f"[component-models] найдено моделей: {len(models_list)} user={current_user.username} role={current_user.role}")
#         return {"component_models": models_list}
#     except Exception as e:
#         logger.error(f"[component-models] ошибка: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
#         raise HTTPException(status_code=500, detail=str(e))


@router.post("/archive-component-info", response_model=List[schemas.ComponentSearchResponseItem])
def get_archive_component_by_filters(
    filters: schemas.ComponentInfoRequest,
    current_user: models.UserDB = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    logger.info(f"[component-info] запрос filters={filters.dict()} user={current_user.username} role={current_user.role}")
    try:
        response = crud.search.get_archive_component_by_filters(
            db,
            trac_model=filters.trac_model,
            type_comp=filters.type_comp,
            name_comp=filters.name_comp,
            producers=filters.producers,
            status=filters.status
        )
        logger.info(f"[component-info] успешно выполнена, найдено записей: {len(response)} user={current_user.username} role={current_user.role}")
        return response
    except Exception as e:
        logger.error(f"[component-info] ошибка: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    


@router.patch("/firmware/{firmware_id}/archive")
def change_firmware_archive_status(
    firmware_id: int,
    request: schemas.ArchiveChangeRequest,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """
    Изменение статуса архивации ПО
    
    - **firmware_id**: ID программного обеспечения
    - **is_archive**: true - переместить в архив, false - восстановить из архива
    """
    logger.info(f"[change_archive] запрос firmware_id={firmware_id} is_archive={request.is_archive} user={current_user.username} role={current_user.role}")
    
    try:
        # Проверяем права доступа (только engineer или moderator)
        if current_user.role not in ['moderator']:
            raise HTTPException(
                status_code=403,
                detail="Недостаточно прав для изменения статуса архивации"
            )
        
        # Находим ПО
        firmware = db.query(models.Software).filter(models.Software.id == firmware_id).first()
        
        if not firmware:
            logger.warning(f"[change_archive] ПО не найдено id={firmware_id}")
            raise HTTPException(
                status_code=404,
                detail=f"ПО с ID {firmware_id} не найдено"
            )
        
        # Изменяем статус архивации
        old_status = firmware.is_archive
        firmware.is_archive = request.is_archive
        
        # Если перемещаем в архив, возможно также меняем is_actual
        if request.is_archive:
            firmware.is_actual = False
        else:
            firmware.is_archive = True
        
        db.commit()
        db.refresh(firmware)
        
        logger.info(f"[change_archive] успешно изменен статус: {old_status} -> {firmware.is_archive}")
        
        return {
            "id": firmware.id,
            "is_archive": firmware.is_archive,
            "is_actual": firmware.is_actual,
            "message": f"ПО успешно {'перемещено в архив' if request.is_archive else 'восстановлено из архива'}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[change_archive] ошибка: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
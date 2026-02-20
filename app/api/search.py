from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from sqlalchemy.orm import Session

from .. import schemas, crud, models
from ..database import get_session
from ..authorization import require_role, get_password_hash, get_current_user
from ..log import logger
from typing import List
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(prefix="/search", tags=["Search"])

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
            model_comp=filters.model_comp,
            producers=filters.producers # добавил producers
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
    if not request.vins:
        return []
    query = db.query(
        models.Tractors.vin,
        models.Component.type.label("component_type"),
        models.Component.model.label("comp_model")
    ).select_from(models.Tractors)\
     .join(models.TelemetryComponents, models.Tractors.id == models.TelemetryComponents.tractor)\
     .join(models.Component, models.TelemetryComponents.component == models.Component.id)\
     .filter(models.Tractors.vin.in_(request.vins))
    
    results = query.all()
    return [
        {
            "vin": r.vin,
            "component_type": r.component_type,
            "comp_model": r.comp_model
        }
        for r in results
    ]

# @router.get("/search-tractor", response_model=List[schemas.TractorSearchResponse])
# def get_search_tractors(
#     request: str, 
#     db: Session = Depends(get_session),
#     current_user: models.UserDB = Depends(get_current_user)
# ):
#     logger.info(f"[search-tractor] запрос={request} user={current_user.username} role={current_user.role}")
#     try:
#         return crud.search.search_tractors(db, request=request)
#     except ValueError as ve:
#         logger.error(f"[search-tractor] ошибка: {str(ve)} user={current_user.username} role={current_user.role}", exc_info=True)
#         raise HTTPException(status_code=400, detail=str(ve))
#     except Exception as e:
#         logger.error(f"[search-tractor] неизвестная ошибка: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
#         raise HTTPException(status_code=500, detail=str(e))
    

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

@router.post("/component-models")
def get_component_models(
    request: schemas.RequestModel,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    logger.info(f"[component-models] запрос={request.dict()} user={current_user.username} role={current_user.role}")
    try:
        models_list = crud.components.get_agg_by_trac_and_comp(
            db,
            request.trac_model if request.trac_model else None,
            None,
            producers=request.producers if request.producers else None # добавил producers
        )
        logger.info(f"[component-models] найдено моделей: {len(models_list)} user={current_user.username} role={current_user.role}")
        return {"component_models": models_list}
    except Exception as e:
        logger.error(f"[component-models] ошибка: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/component-parts")
def get_component_with_part(db: Session = Depends(get_session)):
    try:
        result = crud.search.get_all_components_with_part(db)
        logger.info(f"[component-parts/all] получено записей: {len(result)} user=anonymous role=anonymous")
        return result
    except Exception as e:
        logger.error(f"[component-parts/all] ошибка: {str(e)} user=anonymous role=anonymous", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    


@router.get("/get-po-by-vin/{id}/metadata", response_model=schemas.SoftwareSchema)
def get_tractor_by_id(id: int, db: Session = Depends(get_session), current_user: models.UserDB = Depends(get_current_user)):
    try:
        result = crud.software.get_software_by_id(db, id)
        logger.info(f"[get-po-by-vin] успешно выполнена id={id} user={current_user.username} role={current_user.role}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[software/metadata] ошибка: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
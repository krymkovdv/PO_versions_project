from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from . import CRUDs, schemas, config, models 
from .config import settings 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Query
from typing import List


router = APIRouter()

url_db = config.settings.get_url()
engine = create_engine(url_db)
SessionLocal = sessionmaker(bind=engine)

def get_session():
    with SessionLocal() as session:
        yield session


#Routes трактора
@router.get("/tractors/", response_model=list[schemas.TractorsSchema])
def get_tractors(db: Session = Depends(get_session)):
    try: 
        return CRUDs.get_tractors(db)
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

@router.post("/tractors/", response_model=schemas.TractorsSchema, status_code=status.HTTP_201_CREATED)
def create_tractor(tractor: schemas.TractorsSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат terminal_id
    if CRUDs.get_tractor_by_terminal(db, tractor.id):
        raise HTTPException(status_code=400, detail="Tractor with this terminal_id already exists")
    return CRUDs.create_tractor(db, tractor)

@router.delete("/tractors/{tractor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tractor(tractor_id: int, db: Session = Depends(get_session)):
    success = CRUDs.delete_tractor(db, tractor_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tractor not found")

#Routes компонентов трактора
@router.get("/component/", response_model=list[schemas.ComponentSchema])
def get_component(session: Session = Depends(get_session)):
    try:
        return CRUDs.get_component(session)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении компонентов тракторов: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )

@router.post("/component/", response_model=schemas.ComponentSchema, status_code=status.HTTP_201_CREATED)
def create_component(component: schemas.ComponentSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат terminal_id
    if CRUDs.get_component_by_terminal(db, component.id):
        raise HTTPException(status_code=400, detail="Tractor component with this terminal_id already exists")
    return    CRUDs.create_component(db, component)


@router.delete("/component/{row_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_component(id: int, db: Session = Depends(get_session)):
    success = CRUDs.delete_component(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Tractor component not found")


# #Routes for Telemetry components
@router.get("/telemetryComponents/", response_model=list[schemas.TelemetryComponentSchema])
def get_telemetry_components(session: Session = Depends(get_session)): 
    try:
        return CRUDs.get_telemetry_component(session)
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
    
@router.post("/telemetryComponent/", response_model=schemas.TelemetryComponentSchema, status_code=status.HTTP_201_CREATED)
def create_telemetry_component(telemetry_component: schemas.TelemetryComponentSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат terminal_id
    if CRUDs.get_telemetry_component_by_terminal(db, telemetry_component.id):
        raise HTTPException(status_code=400, detail="Telemetry with this id already exists")
    return    CRUDs.create_telemetry_component(db, telemetry_component)


@router.delete("/telemetryComponent/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_telemetry_component(id: int, db: Session = Depends(get_session)):
    success = CRUDs.delete_telemetry_component(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Telemetry not found")


# #Routes Software
@router.get("/software/", response_model=list[schemas.SoftwareSchema])
def get_software(session: Session = Depends(get_session)):
    try:
        return CRUDs.get_software(session)
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

@router.get("/software/download/{id}")
def download_software(id: int, db: Session = Depends(get_session)):
    fw = CRUDs.download_software(db, id)
    if not fw:
        return HTTPException(status_code=400, detail="Software with this id doesnt exist")
    return {"download_url": fw.path, "filename": f"{fw.name}.bin"}

@router.post("/software/", response_model=schemas.SoftwareSchema, status_code=status.HTTP_201_CREATED)
def create_software(software: schemas.SoftwareSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат terminal_id
    if CRUDs.get_software_by_terminal(db, software.id):
        raise HTTPException(status_code=400, detail="Firmware with this terminal_id already exists")
    return    CRUDs.create_software(db, software)

@router.delete("/software/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_software(id: int, db: Session = Depends(get_session)):
    success = CRUDs.delete_software(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Firmware not found")
    
#routes for ComponentParts
@router.get("/componentParts/", response_model=list[schemas.ComponentPartSchema])
def get_components_parts(session: Session = Depends(get_session)): 
    try:
        return CRUDs.get_componentPart(session)
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
    
@router.post("/componentParts/", response_model=schemas.ComponentPartSchema, status_code=status.HTTP_201_CREATED)
def create_components_parts(component: schemas.ComponentPartSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат terminal_id
    if CRUDs.get_componentPart_by_terminal(db, component.id):
        raise HTTPException(status_code=400, detail="Relations with this id already exists")
    return    CRUDs.create_componentPart(db, component)


@router.delete("/componentParts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_componentPart(id: int, db: Session = Depends(get_session)):
    success = CRUDs.delete_componentPart(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Relations not found")


#routes for ComponentsSoftware
@router.get("/software2components/", response_model=list[schemas.SoftwareComponentsSchema])
def get_Software2Components(session: Session = Depends(get_session)): 
    try:
        return CRUDs.get_software_componentParts(session)
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
    
@router.post("/software2components/", response_model=schemas.SoftwareComponentsSchema, status_code=status.HTTP_201_CREATED)
def create_Software2Components(software_component: schemas.SoftwareComponentsSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат terminal_id
    if CRUDs.get_software_componentsParts_by_terminal(db, software_component.id):
        raise HTTPException(status_code=400, detail="Software_components with this id already exists")
    return    CRUDs.create_software_componentsParts(db, software_component)

@router.delete("/softwareComponents/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_Software2Components(id: int, db: Session = Depends(get_session)):
    success = CRUDs.delete_software_components(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Software_components not found")
    
@router.post("/component-info")
def get_component_by_filters(filters: schemas.ComponentInfoRequest, db: Session = Depends(get_session)):
    data = CRUDs.get_component_by_filters(
        db,
        trac_model=filters.trac_model,
        type_comp=filters.type_comp,
        model_comp=filters.model_comp
    )
    return data

# # #Routes БОЛЬШОЙ ПОИСК
# @router.post("/Search", response_model=List[schemas.TractorSoftwareResponse])
# def get_Search(
#     filters: schemas.TractorFilter,
#     db: Session = Depends(get_session)
# ):
#     try:
#         return CRUDs.get_tractor_software(db, filters)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Ошибка при поиске: {str(e)}")
    
# @router.get("/Tractors/Components", response_model=schemas.TractorSoftwareResponse)
# def tractor_component_by_vin(vin: str, db: Session = Depends(get_session)):
#     try:
#         return CRUDs.get_tractor_component_by_vin(vin, db)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Ошибка при поиске: {str(e)}")
    
# @router.get("/component-version/type")
# def get_component_version_by_types(types: str, db: Session = Depends(get_session)):
#     if not types.strip():
#         raise HTTPException(status_code=400, detail="Параметр 'types' не может быть пустым")
    
#     type_comps = [t.strip() for t in types.split(',') if t.strip()]
#     if not type_comps:
#         raise HTTPException(status_code=400, detail="Не указаны типы компонентов")

#     component_info = CRUDs.get_component_version_by_types(db, type_comps)
#     if not component_info:
#         raise HTTPException(status_code=404, detail=f"Компоненты типов '{types}' не найдены")
    
#     return component_info
    
# @router.get("/component-version/models")
# def get_component_version_by_models(model: str, db: Session = Depends(get_session)):
#     if not model.strip():
#         raise HTTPException(status_code=400, detail="Параметр 'models' не может быть пустым")
    
#     model_comps = [t.strip() for t in model.split(',') if t.strip()]
#     if not model_comps:
#         raise HTTPException(status_code=400, detail="Не указана модель компонентов")

#     component_info = CRUDs.get_component_version_by_models(db, model)
#     if not component_info:
#         raise HTTPException(status_code=404, detail=f"Модель '{model}' не найдены")
    
#     return component_info

# @router.get("/component-version/models&types")
# def get_component_version_by_types_and_models(model: str, type:str, db: Session = Depends(get_session)):
#     if not model.strip():
#         raise HTTPException(status_code=400, detail="Параметр 'models' не может быть пустым")
    
#     if not type.strip():
#         raise HTTPException(status_code=400, detail="Параметр 'types' не может быть пустым")
    
#     model_comps = [t.strip() for t in model.split(',') if t.strip()]
#     if not model_comps:
#         raise HTTPException(status_code=400, detail="Не указана модель компонентов")
    
#     type_comps = [t.strip() for t in type.split(',') if t.strip()]
#     if not type_comps:
#         raise HTTPException(status_code=400, detail="Не указаны типы компонентов")

#     component_info = CRUDs.get_component_version_by_type_models(db, model, type)
#     if not component_info:
#         raise HTTPException(status_code=404, detail=f"Модель '{model}' не найдены")
    
#     return component_info

# @router.get("/component-version/all/")
# def get_all_components_endpoint(db: Session = Depends(get_session)):
#     """
#     Получить информацию о всех компонентах
#     """
#     try:
#         components_info = CRUDs.get_all_components(db)
#         if not components_info:
#             raise HTTPException(status_code=404, detail="Компоненты не найдены")
        
#         return components_info
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")    
        
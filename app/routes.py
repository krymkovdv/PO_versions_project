from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from . import CRUDs, schemas, config, models 
from .config import settings 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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


# Эндпоинт 3: Умный поиск
@router.post("/tractors/search")
def smart_search_tractors(query: str, db: Session = Depends(get_session)):
    tractors = CRUDs.smart_search_tractors(db, query)
    return [{"terminal_id": t.id, "model": t.model, "vin": t.vin, "assemble": t.assembly_date, "last activity": t.last_activity} for t in tractors]


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
    
#routes for Relations
@router.get("/relations/", response_model=list[schemas.RelationSchema])
def get_relations(session: Session = Depends(get_session)): 
    try:
        return CRUDs.get_relations(session)
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
    
@router.post("/relations/", response_model=schemas.RelationSchema, status_code=status.HTTP_201_CREATED)
def create_relations(relation: schemas.RelationSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат terminal_id
    if CRUDs.get_relations_by_terminal(db, relation.id):
        raise HTTPException(status_code=400, detail="Relations with this id already exists")
    return    CRUDs.create_relations(db, relation)


@router.delete("/relations/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_relations(id: int, db: Session = Depends(get_session)):
    success = CRUDs.delete_relations(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Relations not found")


#routes for ComponentsSoftware
@router.get("/softwareComponents/", response_model=list[schemas.SoftwareComponentsSchema])
def get_SoftwareComponents(session: Session = Depends(get_session)): 
    try:
        return CRUDs.get_software_components(session)
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
    
@router.post("/softwareComponents/", response_model=schemas.SoftwareComponentsSchema, status_code=status.HTTP_201_CREATED)
def create_SoftwareComponents(software_component: schemas.SoftwareComponentsSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат terminal_id
    if CRUDs.get_software_components_by_terminal(db, software_component.id):
        raise HTTPException(status_code=400, detail="Software_components with this id already exists")
    return    CRUDs.create_software_components(db, software_component)

@router.delete("/softwareComponents/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_SoftwareComponents(id: int, db: Session = Depends(get_session)):
    success = CRUDs.delete_software_components(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Software_components not found")

# #Routes БОЛЬШОЙ ПОИСК
@router.post("/Search", response_model=List[schemas.TractorSoftwareResponse])
def get_Search(
    filters: schemas.TractorFilter,
    db: Session = Depends(get_session)
):
    try:
        return CRUDs.get_tractor_software(db, filters)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при поиске: {str(e)}")
    
@router.get("/Tractors/Components", response_model=schemas.TractorSoftwareResponse)
def tractor_component_by_vin(vin: str, db: Session = Depends(get_session)):
    try:
        return CRUDs.get_tractor_component_by_vin(vin, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при поиске: {str(e)}")
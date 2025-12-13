from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from . import CRUDs, schemas, config, models, authorization
from .config import settings 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Query
from typing import List, Optional
from .authorization import authenticate_user, create_access_token, require_role, get_password_hash
from .database import get_session
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import date
from fastapi.responses import FileResponse

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()

# Авторизация
@router.get("/users/", response_model=List[schemas.UserSchema], dependencies=[Depends(require_role("moderator"))])
def get_users(db: Session = Depends(get_session)):
    try: 
        return CRUDs.get_users(db)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении пользователей: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )

@router.post("/token/")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/users/", status_code=201, dependencies=[Depends(require_role("moderator"))])
def post_user(user: schemas.UserCreate, db: Session = Depends(get_session)):
    return CRUDs.create_user(db, user)

@router.delete("/users/{user_id}", dependencies=[Depends(require_role("moderator"))])
def delete_user(user_id: int, db: Session = Depends(get_session)):
    if CRUDs.delete_users(db, user_id):
        return {"message": f"User {user_id} deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="User not found")
    
# Routes трактора
@router.get("/tractors/", response_model=List[schemas.TractorsSchema])
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

@router.post("/tractors/", response_model=schemas.TractorsSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("moderator"))])
def create_tractor(tractor: schemas.TractorsSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат vin
    existing = db.query(models.Tractors).filter(models.Tractors.vin == tractor.vin).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tractor with this VIN already exists")
    try:
        return CRUDs.create_tractor(db, tractor)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при создании трактора: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )

@router.delete("/tractors/{tractor_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("moderator"))])
def delete_tractor(tractor_id: int, db: Session = Depends(get_session)):
    success = CRUDs.delete_tractor(db, tractor_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tractor not found")

# Routes компонентов трактора
@router.get("/components/", response_model=List[schemas.ComponentSchema])
def get_components(session: Session = Depends(get_session)):
    try:
        return CRUDs.get_components(session)
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

@router.post("/components/", response_model=schemas.ComponentSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("moderator"))])
def create_component(component: schemas.ComponentSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат model
    existing = db.query(models.Component).filter(models.Component.model == component.model).first()
    if existing:
        raise HTTPException(status_code=400, detail="Component with this model already exists")
    try:
        return CRUDs.create_component(db, component)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при создании компонента: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )

@router.delete("/components/{component_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("moderator"))])
def delete_component(component_id: int, db: Session = Depends(get_session)):
    success = CRUDs.delete_component(db, component_id)
    if not success:
        raise HTTPException(status_code=404, detail="Component not found")

# Routes for Telemetry Components
@router.get("/telemetry-components/", response_model=List[schemas.TelemetryComponentSchema])
def get_telemetry_components(session: Session = Depends(get_session)): 
    try:
        return CRUDs.get_telemetry_components(session)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении телеметрии: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )
    
@router.post("/telemetry-components/", response_model=schemas.TelemetryComponentSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("moderator"))])
def create_telemetry_component(telemetry_component: schemas.TelemetryComponentSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат comp_ser_num
    if telemetry_component.comp_ser_num:
        existing = db.query(models.TelemetryComponents).filter(models.TelemetryComponents.comp_ser_num == telemetry_component.comp_ser_num).first()
        if existing:
            raise HTTPException(status_code=400, detail="Telemetry with this serial number already exists")
    try:
        return CRUDs.create_telemetry_component(db, telemetry_component)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при создании телеметрии: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )

@router.delete("/telemetry-components/{telemetry_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("moderator"))])
def delete_telemetry_component(telemetry_id: int, db: Session = Depends(get_session)):
    success = CRUDs.delete_telemetry_component(db, telemetry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Telemetry not found")

# Routes Software
@router.get("/software/", response_model=List[schemas.SoftwareSchema])
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
    
@router.post("/software/", response_model=schemas.SoftwareSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("moderator"))])
def create_software(software: schemas.SoftwareSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат name или path
    existing = db.query(models.Software).filter(
        (models.Software.name == software.name) | (models.Software.path == software.path)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Software with this name or path already exists")
    try:
        return CRUDs.create_software(db, software)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при создании прошивки: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )

@router.delete("/software/{software_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("moderator"))])
def delete_software(software_id: int, db: Session = Depends(get_session)):
    success = CRUDs.delete_software(db, software_id)
    if not success:
        raise HTTPException(status_code=404, detail="Software not found")
    
# Routes for Component Parts
@router.get("/component-parts/", response_model=List[schemas.ComponentPartSchema])
def get_components_parts(session: Session = Depends(get_session)): 
    try:
        return CRUDs.get_component_parts(session)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении компонентов частей: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )
    
@router.post("/component-parts/", response_model=schemas.ComponentPartSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("moderator"))])
def create_component_parts(part: schemas.ComponentPartSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат part_number + component (если нужно)
    existing = db.query(models.ComponentParts).filter(
        models.ComponentParts.component == part.component,
        models.ComponentParts.part_number == part.part_number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Component part with this number already exists for this component")
    try:
        return CRUDs.create_component_part(db, part)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при создании части компонента: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )

@router.delete("/component-parts/{part_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("moderator"))])
def delete_component_part(part_id: int, db: Session = Depends(get_session)):
    success = CRUDs.delete_component_part(db, part_id)
    if not success:
        raise HTTPException(status_code=404, detail="Component part not found")

# Routes for Software2ComponentPart
@router.get("/software-component-links/", response_model=List[schemas.SoftwareComponentsSchema])
def get_software_component_links(session: Session = Depends(get_session)): 
    try:
        return CRUDs.get_software_component_parts(session)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении связей ПО и частей: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )
    
@router.post("/software-component-links/", response_model=schemas.SoftwareComponentsSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("moderator"))])
def create_software_component_link(link: schemas.SoftwareComponentsSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат связки component_part_id + software_id
    existing = db.query(models.Software2ComponentPart).filter(
        models.Software2ComponentPart.component_part_id == link.component_part_id,
        models.Software2ComponentPart.software_id == link.software_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Link between this component part and software already exists")
    try:
        return CRUDs.create_software_component_part(db, link)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при создании связи ПО и части: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )

@router.delete("/software-component-links/{link_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("moderator"))])
def delete_software_component_link(link_id: int, db: Session = Depends(get_session)):
    success = CRUDs.delete_software_component_part(db, link_id)
    if not success:
        raise HTTPException(status_code=404, detail="Software component link not found")
#------------Routes для страниц-----------------

@router.post("/component-info", response_model=List[schemas.ComponentSearchResponseItem])
def get_component_by_filters(filters: schemas.ComponentInfoRequest, db: Session = Depends(get_session)):
    try:
        return CRUDs.get_component_by_filters(
            db,
            trac_model=filters.trac_model,
            type_comp=filters.type_comp,
            model_comp=filters.model_comp
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-component", response_model=List[schemas.ComponentSearchResponseItem])
def get_search_component(query: str, db: Session = Depends(get_session)):
    try:
        return CRUDs.search_components(db, model_comp=query)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Страница 4: Поиск тракторов ---
@router.post("/tractor-info", response_model=List[schemas.TractorSearchResponse])
def get_tractors_by_filters(filters: schemas.TractorFilter, db: Session = Depends(get_session)):
    try:
        print("Received filters:", filters.dict())
        data = CRUDs.get_tractors_by_filters(db, filters)
        print("Data count:", len(data))
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-tractor", response_model=List[schemas.TractorSearchResponse])
def get_search_tractors(request: str, db: Session = Depends(get_session)):
    try:
        return CRUDs.search_tractors(db, request=request)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-tractor-vin", response_model=List[schemas.TractorSearchResponse2])
def get_search_tractors_vin(request: str, db: Session = Depends(get_session)):
    try:
        return CRUDs.get_tractor_by_vin(db, vin=request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Загрузка и скачивание ПО ---
@router.post(
    "/software/assign",
    response_model=schemas.SoftwareResponse,
    status_code=201,
)
def assign_software_to_components_route(
    file: UploadFile = File(...),
    name: str = Form(...),
    is_major: bool = Form(...),
    inner_name: Optional[str] = Form(None),
    release_date: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    component_models: List[str] = Form(...),
    part_number: List[int] = Form(...),
    db: Session = Depends(get_session)
):
    rd = None
    if release_date:
        try:
            rd = date.fromisoformat(release_date)
        except ValueError:
            raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")

    software_data = schemas.AssignSoftwareRequest(
        name=name,
        is_major=is_major,
        inner_name=inner_name,
        release_date=rd,
        description=description,
        component_models=component_models,
        part_number=part_number
    )

    try:
        return CRUDs.assign_software_to_components(db, file=file, software_data=software_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении ПО: {str(e)}")

@router.get("/software/download/{id}", response_class=FileResponse)
def download_software_file(id: int, db: Session = Depends(get_session)):
    try:
        metadata = CRUDs.get_software_metadata(db, id)
        file_path = CRUDs.get_software_file_path(db, id)

        return FileResponse(
            path=file_path,
            filename=metadata.filename_for_download,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{metadata.filename_for_download}"',
                "X-Software-ID": str(metadata.id),
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/software/{id}/metadata", response_model=schemas.SoftwareMetadata)
def get_software_metadata(id: int, db: Session = Depends(get_session)):
    try:
        return CRUDs.get_software_metadata(db, id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.head("/software/download/{id}")
def check_software_file(id: int, db: Session = Depends(get_session)):
    try:
        file_info = CRUDs.get_software_file_info(db, id)
        return {
            "exists": file_info.exists,
            "size": file_info.size_bytes,
            "path": file_info.full_path
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/component-models")
def get_component_models(request: schemas.RequestModel, db: Session = Depends(get_session)):
    try:
        models_list = CRUDs.get_agg_by_trac_and_comp(
            db,
            request.trac_model if request.trac_model else None,
            None  # type_comp не передаётся
        )
        return {"component_models": models_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/component-parts")
def get_component_with_part(db: Session = Depends(get_session)):
    try:
        result = CRUDs.get_all_components_with_part(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
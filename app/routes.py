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
@router.get("/users/", response_model=list[schemas.UserSchema], dependencies=[Depends(require_role("moderator"))])
def get_users(db: Session = Depends(get_session)):
    try: 
        return CRUDs.get_users(db)
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

@router.post("/token/")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/users/", status_code=201, dependencies=[Depends(require_role("moderator"))])
def post_user(user: schemas.UserCreate, db: Session = Depends(get_session)):
    existing = db.query(models.UserDB).filter(models.UserDB.username == user.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")
    user_in = models.UserDB(
        username=user.username,
        password_hash=get_password_hash(user.password),
        role=user.role
    )
    db.add(user_in)
    db.commit()
    db.refresh(user_in)
    return {"username": user_in.username, "role": user_in.role}

@router.delete("/users/", dependencies=[Depends(require_role("moderator"))])
def delete_user(id: int, db: Session = Depends(get_session)):
    if CRUDs.delete_users(db, id):
        return {"message": f"User {id} deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="User not found")
    
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

@router.post("/tractors/", response_model=schemas.TractorsSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("moderator"))])
def create_tractor(tractor: schemas.TractorsSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат terminal_id
    if CRUDs.get_tractor_by_terminal(db, tractor.id):
        raise HTTPException(status_code=400, detail="Tractor with this terminal_id already exists")
    return CRUDs.create_tractor(db, tractor)

@router.delete("/tractors/{tractor_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("moderator"))])
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

@router.post("/component/", response_model=schemas.ComponentSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("moderator"))])
def create_component(component: schemas.ComponentSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат terminal_id
    if CRUDs.get_component_by_terminal(db, component.id):
        raise HTTPException(status_code=400, detail="Tractor component with this terminal_id already exists")
    return    CRUDs.create_component(db, component)


@router.delete("/component/{row_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("moderator"))])
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
    
@router.post("/telemetryComponent/", response_model=schemas.TelemetryComponentSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("moderator"))])
def create_telemetry_component(telemetry_component: schemas.TelemetryComponentSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат terminal_id
    if CRUDs.get_telemetry_component_by_terminal(db, telemetry_component.id):
        raise HTTPException(status_code=400, detail="Telemetry with this id already exists")
    return    CRUDs.create_telemetry_component(db, telemetry_component)


@router.delete("/telemetryComponent/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("moderator"))])
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
    
@router.post("/software/", response_model=schemas.SoftwareSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("moderator"))])
def create_software(software: schemas.SoftwareSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат terminal_id
    if CRUDs.get_software_by_terminal(db, software.id):
        raise HTTPException(status_code=400, detail="Firmware with this terminal_id already exists")
    return    CRUDs.create_software(db, software)

@router.delete("/software/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("moderator"))])
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
    
@router.post("/componentParts/", response_model=schemas.ComponentPartSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("moderator"))])
def create_components_parts(component: schemas.ComponentPartSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат terminal_id
    if CRUDs.get_componentPart_by_terminal(db, component.id):
        raise HTTPException(status_code=400, detail="Relations with this id already exists")
    return    CRUDs.create_componentPart(db, component)


@router.delete("/componentParts/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("moderator"))])
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
    
@router.post("/software2components/", response_model=schemas.SoftwareComponentsSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("moderator"))])
def create_Software2Components(software_component: schemas.SoftwareComponentsSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат terminal_id
    if CRUDs.get_software_componentsParts_by_terminal(db, software_component.id):
        raise HTTPException(status_code=400, detail="Software_components with this id already exists")
    return    CRUDs.create_software_componentsParts(db, software_component)

@router.delete("/softwareComponents/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("moderator"))])
def delete_Software2Components(id: int, db: Session = Depends(get_session)):
    success = CRUDs.delete_software_components(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Software_components not found")


#------------Routes для страниц-----------------

#3-я страница
#Поиск по фильтрам КОМПОНЕНТОВ
@router.post("/component-info")
def get_component_by_filters(filters: schemas.ComponentInfoRequest, db: Session = Depends(get_session), response_model=List[schemas.ComponentSearchResponseItem]):
    query = CRUDs.get_component_by_filters(
        db,
        trac_model=filters.trac_model,
        type_comp=filters.type_comp,
        model_comp=filters.model_comp
    )
    return query

#Глобальный поиск Компонентов
@router.get("/search-component", response_model=List[schemas.ComponentSearchResponseItem])
def get_Search_Component(
    query: str,
    db: Session = Depends(get_session),
):
    data = CRUDs.search_components(model_comp=query, db=db)
    return data

#4-я страница
#Поиск по фильтрам ТРАКТОРОВ
@router.post("/tractor-info", response_model=List[schemas.TractorSearchResponse] )
def get_tractors_by_filters(filters: schemas.TractorFilter, db: Session = Depends(get_session)):
    data = CRUDs.get_tractors_by_filters(db,filters)
    return data

#Глобальный поиск тракторов
@router.get("/search-tractor", response_model=List[schemas.TractorSearchResponse])
def get_Search_Tractors(
    request: str,
    db: Session = Depends(get_session),
):
    data = CRUDs.search_tractors(request=request, db=db)
    return data

#Поиск по vinу для Трактора
@router.get("/search-tractor-vin", response_model=List[schemas.TractorSearchResponse])
def get_Search_Tractors_vin(
    request: str,
    db: Session = Depends(get_session),
):
    data = CRUDs.get_tractor_by_vin(vin=request, db=db)
    return data

#Добавление и скачка ПО
@router.post(
    "/software/upload", 
    response_model=schemas.SoftwareResponse,  
    status_code=201
)
def upload_software(
    file: UploadFile = File(...),
    name: str = Form(...),
    inner_name: Optional[str] = Form(None),
    release_date: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_session)
):
    try:
        rd = date.fromisoformat(release_date) if release_date else None
    except ValueError:
        raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")
    
    software_data = schemas.UploadSoftwareRequest(
        name=name,
        inner_name=inner_name,
        release_date=rd,
        description=description
    )
    

    if file.size > config.MAX_FILE_SIZE:
        raise HTTPException(400, "File too large")
    
    file_bytes = file.file.read() 
    
    result = CRUDs.upload_software(
        db=db,
        file_data=file_bytes,
        file_name=file.filename,
        software_data=software_data
    )
    
    return result

@router.get("/software/download/{id}", response_class=FileResponse)
def download_software_file(id: int, db: Session = Depends(get_session)):
    """
    Скачивание ПО: возвращает файл через FileResponse.
    """
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

# Опционально: эндпоинт для получения метаданных (без скачивания)
@router.get("/software/{id}/metadata", response_model=schemas.SoftwareMetadata)
def get_software_metadata(id: int, db: Session = Depends(get_session)):
    return CRUDs.get_software_metadata(db, id)

# Опционально: эндпоинт для проверки файла
@router.head("/software/download/{id}")
def check_software_file(id: int, db: Session = Depends(get_session)):
    file_info = CRUDs.get_software_file_info(db, id)
    return {
        "exists": file_info.exists,
        "size": file_info.size_bytes,
        "path": file_info.full_path
    }
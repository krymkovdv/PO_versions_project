from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from sqlalchemy.orm import Session

from .. import schemas, crud, models
from ..database import get_session
from ..authorization import require_role, get_current_user
from ..log import logger
from typing import Optional, Union, List, Annotated
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import FileResponse, Response
from datetime import datetime
import os


router = APIRouter(prefix="/software", tags=["Software"])

@router.get("", response_model=List[schemas.SoftwareSchema])
def get_software(
    session: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    try:
        logger.info(f"[get_software] успешно выполнена user={current_user.username} role={current_user.role}")
        return crud.software.get_software(session)
    except SQLAlchemyError as e:
        logger.error(f"[get_software] ошибка SQLAlchemy: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении прошивок: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[get_software] неизвестная ошибка: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )
    
@router.post("", response_model=schemas.SoftwareSchema, status_code=status.HTTP_201_CREATED,dependencies=[Depends(require_role("moderator"))])
def create_software(software: schemas.SoftwareSchema, db: Session = Depends(get_session), current_user: models.UserDB = Depends(get_current_user)):
    # Проверка на дубликат name или path
    existing = db.query(models.Software).filter(
        (models.Software.id == software.id)
    ).first()
    if existing:
        logger.warning(f"Software с id: {software.id} уже есть user={current_user.username} role={current_user.role}")
        raise HTTPException(status_code=400, detail="Software with this name or path already exists")
    try:
        result = crud.software.create_software(db, software)
        logger.info(f"[create_software] успешно выполнена user={current_user.username} role={current_user.role}")
        return result
    except SQLAlchemyError as e:
        logger.error(f"[create_software] ошибка SQLAlchemy: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при создании прошивки: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[create_software] неизвестная ошибка: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )

@router.delete("/{software_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("moderator"))])
def delete_software(
    software_id: int, 
    db: Session = Depends(get_session), 
    current_user: models.UserDB = Depends(get_current_user)
):
    try:
        success = crud.software.delete_software_with_links(db, software_id)
        if not success:
            logger.warning(f"[delete_software] ПО {software_id} не найдено user={current_user.username}")
            raise HTTPException(status_code=404, detail="Software not found")
        
        logger.info(f"[delete_software] ПО {software_id} удалено user={current_user.username} role={current_user.role}")
        # Возвращаем 204 No Content
        return Response(status_code=status.HTTP_204_NO_CONTENT)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[delete_software] ошибка: {str(e)} user={current_user.username}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении ПО: {str(e)}"
        )

@router.patch("/{sw_id}", response_model=schemas.SoftwareResponse)
def update_software(
    sw_id: int,
    software_update: schemas.SoftwareUpdate,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    if current_user.role != "moderator" and current_user.role != "engineer":
        raise HTTPException(status_code=403, detail="Only moderator can update software")
    return crud.software.update_software(db, sw_id, software_update)


# ============================================
# Связи ПО ↔ Компонент
# ============================================
@router.get("/{software_id}/components", response_model=list[schemas.ComponentSchema])
def get_components_for_software(
    software_id: int,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Получить все компоненты для ПО"""
    components = crud.software_component_link.get_components_for_software(
        db, software_id
    )
    if not components:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No components found for this software"
        )
    return components

@router.post("/{software_id}/components", status_code=201)
def link_component_to_software(
    software_id: int,
    link_data: schemas.SoftwareComponentsSchema,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Связать компонент с ПО"""
    
    # Проверка прав (только engineer или moderator)
    if current_user.role not in ['engineer', 'moderator']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only engineers or moderators can link components"
        )
    
    # Проверка существования ПО
    software = db.query(models.Software).filter(models.Software.id == software_id).first()
    if not software:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Software not found"
        )
    
    # Проверка существования компонента
    component = db.query(models.Component).filter(
        models.Component.id == link_data.component_id
    ).first()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found"
        )
    
    try:
        # Принудительно устанавливаем software_id из URL
        link_data.software_id = software_id
        
        db_link = crud.software_component_link.create_software_component_link(
            db, link_data
        )
        logger.info(
            f"[link_component_to_software] created link "
            f"software_id={software_id}, component_id={link_data.component_id}"
        )
        return {"id": db_link.id, "component_id": db_link.component_id, "software_id": db_link.software_id}
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"[link_component_to_software] error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error linking component: {str(e)}"
        )

@router.delete("/{software_id}/components/{component_id}")
def unlink_component_from_software(
    software_id: int,
    component_id: int,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Удалить связь компонента с ПО"""
    
    # Проверка прав
    if current_user.role not in ['engineer', 'moderator']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only engineers or moderators can unlink components"
        )
    
    success = crud.software_component_link.delete_software_component_link_by_ids(
        db, component_id, software_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    
    logger.info(
        f"[unlink_component_from_software] deleted link "
        f"software_id={software_id}, component_id={component_id}"
    )
    return {"message": "Link deleted successfully"}


@router.get("/links", response_model=list[schemas.SoftwareComponentsSchema])
def get_all_software_component_links(
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Получить все связи ПО ↔ Компонент"""
    return crud.software_component_link.get_all_software_component_links(db)
    
@router.post(
    "/assign",
    response_model=schemas.SoftwareResponse,
    status_code=201,
)
def assign_software_to_components_route(
    file: UploadFile = File(..., description="Файл ПО"),
    instruction_file: Annotated[
        Optional[Union[UploadFile, str]], 
        File(description="Файл инструкции (необязательно)")
    ] = None,
    software_release_date: Optional[str] = Form(None),
    software_description: Optional[str] = Form(None),
    software_is_actual: bool = Form(True),
    software_is_archive: bool = Form(False),
    software_is_critical: bool = Form(False),
    software_status: str = Form("serial"),
    software_tractor_models: str = Form(...),
    software_producer: str = Form(...),
    previous_sw_version: Optional[str] = Form(default=None),
    component_models: str = Form(...),
    component_types: str = Form(...),
    component_producers: str = Form(...),
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """
    Назначение ПО нескольким компонентам и тракторам
    """
    import json

    #Нормализация instruction_file
    def normalize_optional_file(value) -> Optional[UploadFile]:
        """Преобразует undefined/null/пустые значения в None"""
        # Случай 1: уже None
        if value is None:
            return None
        
        # Случай 2: строка "undefined", "null" или пустая
        if isinstance(value, str):
            stripped = value.strip().lower()
            if stripped in ("", "undefined", "null", "none"):
                return None
            # Если пришла непустая строка — это ошибка
            logger.warning(f"[software/assign] instruction_file передан как строка: '{value}'")
            raise HTTPException(
                400,
                detail="instruction_file должен быть файлом, а не строкой"
            )
        
        # Случай 3: UploadFile с пустым именем
        if isinstance(value, UploadFile):
            if not value.filename or not value.filename.strip():
                return None
            return value

        return value
    
    instruction_file = normalize_optional_file(instruction_file)
            
    # 1. Парсинг даты
    rd: Optional[datetime] = None
    if software_release_date:
        try:
            rd = datetime.fromisoformat(software_release_date)
        except ValueError:
            logger.error(f"[software/assign] неверный формат даты: {software_release_date}")
            raise HTTPException(400, "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")
    
    # 2. Helper для парсинга JSON-массивов
    def parse_json_or_string(value: str) -> List[str]:
        if not value or not value.strip():
            return []
        value = value.strip()
        if value.startswith('['):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return [value]
        return [value]
    
    try:
        tractor_models_list = parse_json_or_string(software_tractor_models)
        component_models_list = parse_json_or_string(component_models)
        component_types_list = parse_json_or_string(component_types)
        component_producers_list = parse_json_or_string(component_producers)
        
        if not tractor_models_list:
            raise HTTPException(400, "software_tractor_models is required")
        if not component_models_list:
            raise HTTPException(400, "component_models is required")
        if not component_types_list:
            raise HTTPException(400, "component_types is required")
        if not component_producers_list:
            raise HTTPException(400, "component_producers is required")
    except Exception as e:
        logger.error(f"[software/assign] ошибка парсинга: {str(e)}")
        raise HTTPException(400, f"Invalid format: {str(e)}")
    
    # 3. Валидация статуса
    if software_status not in ["serial", "in operation", "experienced"]:
        raise HTTPException(400, "Invalid status. Must be: 'serial', 'in operation', 'experienced'")
    
    # 4. Парсинг previous_sw_version
    prev_sw_ver_int: Optional[int] = None
    if previous_sw_version and isinstance(previous_sw_version, str):
        stripped = previous_sw_version.strip()
        if stripped:
            try:
                prev_sw_ver_int = int(stripped)
            except ValueError:
                logger.error(f"[software/assign] Неверный previous_sw_version: '{previous_sw_version}'")
                raise HTTPException(
                    400, 
                    detail=f"previous_sw_version должен быть целым числом, получено: '{previous_sw_version}'"
                )
    
    # 5. Создание схемы данных
    software_data = schemas.AssignSoftwareRequest(
        software_release_date=rd,
        software_description=software_description,
        software_is_actual=software_is_actual,
        software_is_archive=software_is_archive,
        software_is_critical=software_is_critical,
        software_status=software_status,
        software_tractor_models=tractor_models_list,
        software_producer=software_producer,
        software_previous_version=prev_sw_ver_int,  
        component_models=component_models_list,
        component_types=component_types_list,
        component_producers=component_producers_list
    )
    
    # 6. Вызов CRUD
    try:
        logger.info(
            f"[software/assign] producer={software_producer}, "
            f"components={len(component_models_list)}, "
            f"user={current_user.username}, "
            f"instruction={'present' if instruction_file else 'absent'}"
        )
        
        base_name = os.path.splitext(file.filename)[0] if file.filename else "unknown"
        
        return crud.software.assign_software_to_components(
            db,
            file=file,
            software_data=software_data,
            instruction_file=instruction_file,  
            base_name=base_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[software/assign] ошибка: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении ПО: {str(e)}")
    
@router.get("/download/{id}", response_class=FileResponse)
def download_software_file(
    id: int,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Скачать файл ПО"""
    logger.info(f"[software/download] запрос на скачивание id={id} user={current_user.username}")
    try:
        file_info = crud.software.download_software_file(db, id)
        logger.info(f"file_info: {file_info}")  # ДОБАВЬТЕ ЭТО
        logger.info(f"filename: {file_info['filename']}")  # И ЭТО
        return FileResponse(
            path=file_info["file_path"],
            filename=file_info["filename"],
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{file_info["filename"]}"',
                "X-Software-ID": str(file_info["software_id"]),
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[software/download] ошибка: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{id}/instruction", response_class=FileResponse)
def download_instruction_file(
    id: int,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Скачать файл инструкции"""
    logger.info(f"[software/download/instruction] запрос на скачивание инструкции id={id} user={current_user.username}")
    try:
        file_info = crud.software.download_instruction_file(db, id)
        return FileResponse(
            path=file_info["file_path"],
            filename=file_info["filename"],
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{file_info["filename"]}"',
                "X-Software-ID": str(file_info["software_id"]),
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[software/download/instruction] ошибка: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-instruction/{id}", response_model=schemas.SoftwareMetadata, dependencies=[Depends(require_role("moderator"))])
def upload_instruction(
    id: int,
    instruction_file: UploadFile = File(...),
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    """Загрузить/обновить инструкцию для существующего ПО"""
    logger.info(f"[software/upload-instruction] загрузка инструкции для id={id} user={current_user.username}")
    try:
        result = crud.software.update_software_instruction(
            db=db,
            software_id=id,
            instruction_file=instruction_file
        )
        logger.info(f"[software/upload-instruction] успешно загружено user={current_user.username}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[software/upload-instruction] ошибка: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при загрузке инструкции: {str(e)}")

@router.get("/{id}/metadata", response_model=schemas.SoftwareMetadata)
def get_software_metadata(
    id: int,
    db: Session = Depends(get_session)
):
    """Получить метаданные ПО включая информацию об инструкции"""
    try:
        result = crud.software.get_software_metadata(db, id)
        logger.info(f"[software/metadata] получены метаданные id={id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[software/metadata] ошибка: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.head("/download/{id}")
def check_software_file(
    id: int,
    db: Session = Depends(get_session)
):
    """Проверить существование файла ПО"""
    try:
        file_info = crud.software.get_software_file_info(db, id)
        logger.info(f"[software/head] проверка файла id={id}, exists={file_info.exists}")
        return {
            "exists": file_info.exists,
            "size": file_info.size_bytes,
            "path": file_info.full_path
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[software/head] ошибка: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.head("/download/{id}/instruction")
def check_instruction_file(
    id: int,
    db: Session = Depends(get_session)
):
    """Проверить существование файла инструкции"""
    try:
        file_info = crud.software.get_instruction_file_info(db, id)
        logger.info(f"[software/head/instruction] проверка файла id={id}, exists={file_info.exists}")
        return {
            "exists": file_info.exists,
            "size": file_info.size_bytes,
            "path": file_info.full_path,
            "filename": file_info.filename
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[software/head/instruction] ошибка: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
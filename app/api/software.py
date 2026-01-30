from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from sqlalchemy.orm import Session

from .. import schemas, crud, models
from ..database import get_session
from ..authorization import require_role, get_current_user
from ..log import logger
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import FileResponse
from datetime import date

router = APIRouter(prefix="/software", tags=["Software"])

@router.get("/", response_model=List[schemas.SoftwareSchema])
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
    
@router.post("/", response_model=schemas.SoftwareSchema, status_code=status.HTTP_201_CREATED,dependencies=[Depends(require_role("moderator"))])
def create_software(software: schemas.SoftwareSchema, db: Session = Depends(get_session), current_user: models.UserDB = Depends(get_current_user)):
    # Проверка на дубликат name или path
    existing = db.query(models.Software).filter(
        (models.Software.name == software.name) | (models.Software.path == software.path)
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

@router.delete("/{software_id}", status_code=status.HTTP_204_NO_CONTENT,dependencies=[Depends(require_role("moderator"))])
def delete_software(software_id: int, db: Session = Depends(get_session), current_user: models.UserDB = Depends(get_current_user)):
    success = crud.software.delete_software(db, software_id)
    if not success:
        logger.error(f"[delete_software] software с таким id: {software_id} не найден user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(status_code=404, detail="Software not found")
    logger.info(f"[delete_software] software {software_id} удалён user={current_user.username} role={current_user.role}")

@router.patch("/{sw_id}", response_model=schemas.SoftwareResponse)
def update_software(
    sw_id: int,
    software_update: schemas.SoftwareUpdate,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    if current_user.role != "moderator":
        raise HTTPException(status_code=403, detail="Only moderator can update software")
    return crud.software.update_software(db, sw_id, software_update)

@router.get("/software-component-links/", response_model=List[schemas.SoftwareComponentsSchema])
def get_software_component_links(session: Session = Depends(get_session)): 
    try:
        logger.info(f"[get_software-component-links] успешно выполнена user=anonymous role=anonymous")
        return crud.software.get_software_component_parts(session)
    except SQLAlchemyError as e:
        logger.error(f"[get_software-component-links] ошибка SQLAlchemy: {str(e)} user=anonymous role=anonymous", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении связей ПО и частей: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[get_software-component-links] неизвестная ошибка: {str(e)} user=anonymous role=anonymous", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )
    
@router.post("/software-component-links/", response_model=schemas.SoftwareComponentsSchema, status_code=status.HTTP_201_CREATED,dependencies=[Depends(require_role("moderator"))])
def create_software_component_link(link: schemas.SoftwareComponentsSchema, db: Session = Depends(get_session), current_user: models.UserDB = Depends(get_current_user)):
    # Проверка на дубликат связки component_part_id + software_id
    existing = db.query(models.Software2ComponentPart).filter(
        models.Software2ComponentPart.component_part_id == link.component_part_id,
        models.Software2ComponentPart.software_id == link.software_id
    ).first()
    if existing:
        logger.warning(f"[post_software-component-links] связь уже есть user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(status_code=400, detail="Link between this component part and software already exists")
    try:
        result = crud.software.create_software_component_part(db, link)
        logger.info(f"[post_software-component-links] успешно выполнена user={current_user.username} role={current_user.role}")
        return result
    except SQLAlchemyError as e:
        logger.error(f"[post_software-component-links] ошибка SQLAlchemy: {str(e)} user={current_user.username} role={current_user.role}",  exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при создании связи ПО и части: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[post_software-component-links] неизвестная ошибка: {str(e)} user={current_user.username} role={current_user.role}",  exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )

@router.delete("/software-component-links/{link_id}", status_code=status.HTTP_204_NO_CONTENT,dependencies=[Depends(require_role("moderator"))])
def delete_software_component_link(link_id: int, db: Session = Depends(get_session), current_user: models.UserDB = Depends(get_current_user)):
    success = crud.software.delete_software_component_part(db, link_id)
    if not success:
        logger.error(f"[delete_software_component_link] связь {link_id} не найдена user={current_user.username} role={current_user.role}")
        raise HTTPException(status_code=404, detail="Software component link not found")
    logger.info(f"[delete_software_component_link] связь {link_id} удалена user={current_user.username} role={current_user.role}")

@router.post(
    "/assign",
    response_model=schemas.SoftwareResponse,
    status_code=201,
    
)
def assign_software_to_components_route(
    file: UploadFile = File(...),
    name: str = Form(...),
    is_major: bool = Form(...),
    inner_name: str = Form(...),
    release_date: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    component_models: List[str] = Form(...),
    part_type: List[str] = Form(...),
    previous_sw_version_str: Optional[str] = Form(None),
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    rd = None
    if release_date:
        try:
            rd = date.fromisoformat(release_date)
        except ValueError:
            logger.error(f"[software/assign] неверный формат даты: {release_date} user={current_user.username} role={current_user.role}")
            raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")

    prev_sw_ver_int: Optional[int] = None
    if previous_sw_version_str is not None and previous_sw_version_str.strip() != "":
        try:
            prev_sw_ver_int = int(previous_sw_version_str)
        except ValueError:
            raise HTTPException(400, f"previous_sw_version '{previous_sw_version_str}' is not a valid integer user={current_user.username} role={current_user.role}")

    software_data = schemas.AssignSoftwareRequest(
        name=name,
        is_major=is_major,
        inner_name=inner_name,
        release_date=rd,
        description=description,
        component_models=component_models,
        part_type=part_type,
        previous_sw_version=prev_sw_ver_int
    )

    try:
        logger.info(f"[software/assign] имя={name}, is_major={is_major} user={current_user.username} role={current_user.role}")
        return crud.software.assign_software_to_components(db, file=file, software_data=software_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[software/assign] ошибка: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении ПО: {str(e)}")

@router.get("/download/{id}", response_class=FileResponse)
def download_software_file(
    id: int,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    logger.info(f"[software/download] запрос на скачивание id={id} user={current_user.username} role={current_user.role}")
    try:
        metadata = crud.software.get_software_metadata(db, id)
        file_path = crud.software.get_software_file_path(db, id)
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
        logger.error(f"[software/download] HTTP ошибка при скачивании id={id} user={current_user.username} role={current_user.role}")
        raise
    except Exception as e:
        logger.error(f"[software/download] ошибка: {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id}/metadata", response_model=schemas.SoftwareMetadata)
def get_software_metadata(id: int, db: Session = Depends(get_session)):
    try:
        result = crud.software.get_software_metadata(db, id)
        logger.info(f"[software/metadata] получены метаданные id={id} user=anonymous role=anonymous")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[software/metadata] ошибка: {str(e)} user=anonymous role=anonymous", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.head("/download/{id}")
def check_software_file(id: int, db: Session = Depends(get_session)):
    logger.info(f"📥 [DEBUG] Запрос на скачивание id={id}")
    try:
        file_info = crud.software.get_software_file_info(db, id)
        logger.info(f"[software/head] проверка файла id={id}, exists={file_info.exists} user=anonymous role=anonymous")
        return {
            "exists": file_info.exists,
            "size": file_info.size_bytes,
            "path": file_info.full_path
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[software/head] ошибка: {str(e)} user=anonymous role=anonymous", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
@router.patch("/software-component-links/{link_id}", response_model=schemas.SoftwareComponentsSchema)
def update_software_component_link(
    link_id: int,
    link_update: schemas.SoftwareComponentLinkUpdate,
    db: Session = Depends(get_session),
    current_user: models.UserDB = Depends(get_current_user)
):
    if current_user.role != "moderator":
        raise HTTPException(status_code=403, detail="Only moderator can update software-component links")
    return crud.software.update_software_component_part(db, link_id, link_update)
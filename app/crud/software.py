from sqlalchemy.orm import Session
from .. import models, schemas, config
from sqlalchemy import select
from fastapi import HTTPException, status, Depends, Form, File, UploadFile
import uuid
import re
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

#Software
def get_software(db: Session):
    stmt = select(models.Software)
    result = db.execute(stmt).scalars().all()
    return result

def get_software_by_id(db: Session, id: int):
    return db.query(models.Software).filter(models.Software.id == id).first()

def create_software(db: Session, software: schemas.SoftwareSchema):
    db_software = models.Software(
        path=software.path,
        name=software.name,
        inner_name=software.inner_name,
        release_date=software.release_date,
        description=software.description
    )
    db.add(db_software)
    db.commit()
    db.refresh(db_software)
    return db_software

def delete_software(db: Session, id: int):
    software = db.query(models.Software).filter(models.Software.id == id).first()
    if software is None:
        return False
    db.delete(software)
    db.commit()
    return True

#Link Software and ComponentParts
def get_software_component_parts(db: Session):
    stmt = select(models.Software2ComponentPart)
    result = db.execute(stmt).scalars().all()
    return result

def get_software_component_part_by_id(db: Session, id: int):
    return db.query(models.Software2ComponentPart).filter(models.Software2ComponentPart.id == id).first()

def create_software_component_part(db: Session, link: schemas.SoftwareComponentsSchema):
    db_link = models.Software2ComponentPart(
        component_part_id=link.component_part_id,
        software_id=link.software_id,
        is_major=link.is_major,
        status=link.status,
        date_change_major=link.date_change_major,
        not_recom=link.not_recom,
        date_change_record=link.date_change_record,
        previous_sw_version=link.previous_sw_version
    )
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

def delete_software_component_part(db: Session, id: int):
    link = db.query(models.Software2ComponentPart).filter(models.Software2ComponentPart.id == id).first()
    if link is None:
        return False
    db.delete(link)
    db.commit()
    return True

def secure_filename(filename: str) -> str:
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    return filename.strip("._")

def save_uploaded_file(file, filename: str) -> str:
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    safe_filename = f"{uuid.uuid4().hex}_{secure_filename(filename)}"
    file_path = os.path.join(config.UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as f:
        if hasattr(file, 'read'):  # UploadFile
            while chunk := file.file.read(8192):
                f.write(chunk)
        else:  # bytes
            f.write(file)
    return safe_filename

def check_file_size(file: UploadFile, max_size: int) -> int:
    """
    Читает файл по частям и проверяет, не превышает ли его размер max_size.
    Возвращает размер файла или вызывает HTTPException.
    """
    size = 0
    chunk_size = 8192  # 8KB за раз
    original_pos = file.file.tell()
    file.file.seek(0)

    while True:
        chunk = file.file.read(chunk_size)
        if not chunk:
            break
        size += len(chunk)
        if size > max_size:
            file.file.seek(original_pos) 
            raise HTTPException(
                status_code=413,
                detail=f"File size too large: {size + len(chunk)} bytes > {max_size} bytes"
            )

    file.file.seek(original_pos)  
    return size

def assign_software_to_components(
    db: Session,
    file,
    software_data: schemas.AssignSoftwareRequest
) -> schemas.SoftwareResponse:
    check_file_size(file, config.MAX_FILE_SIZE)
    saved_filename = None
    try:
        saved_filename = save_uploaded_file(file, file.filename)

        fw = models.Software(
            path=saved_filename,
            name=software_data.name,
            inner_name=software_data.inner_name,
            release_date=software_data.release_date,
            description=software_data.description
        )
        db.add(fw)
        db.flush()

        n_models = len(software_data.component_models)
        n_parts = len(software_data.part_type)
        if n_models != n_parts:
            raise HTTPException(
                400,
                f"Несоответствие: component_models ({n_models}) и part_type ({n_parts}) должны иметь одинаковую длину"
            )
        if n_models == 0:
            raise HTTPException(400, "Должен быть указан хотя бы один компонент")

        for i in range(n_models):
            comp_model = software_data.component_models[i]
            part_type = software_data.part_type[i]

            component = db.query(models.Component).filter(
                models.Component.model == comp_model
            ).first()
            if not component:
                raise HTTPException(404, f"Component model '{comp_model}' not found")

            part = db.query(models.ComponentParts).filter(
                models.ComponentParts.component == component.id,
                models.ComponentParts.part_type == part_type
            ).first()

            if not part:
                part = models.ComponentParts(
                    component=component.id,
                    part_type=part_type
                )
                db.add(part)
                db.flush()

            link = models.Software2ComponentPart(
                component_part_id=part.id,
                software_id=fw.id, 
                is_major=software_data.is_major,
                status='s',
                date_change_major=datetime.utcnow().date() if software_data.is_major else None,
                previous_sw_version=software_data.previous_sw_version 
            )
            db.add(link)

        db.commit()
        db.refresh(fw)

        return schemas.SoftwareResponse(
            id=fw.id,
            name=fw.name,
            inner_name=fw.inner_name,
            release_date=fw.release_date,
            description=fw.description,
            download_url=f"/software/download/{fw.id}"
        )

    except Exception as e:
        db.rollback()
        if saved_filename:
            path = os.path.join(config.UPLOAD_DIR, saved_filename)
            if os.path.exists(path):
                os.remove(path)
        raise

def get_software_full(db: Session, software_id: int):
    fw = db.query(models.Software).filter(
        models.Software.id == software_id
    ).first()

    if not fw:
        raise HTTPException(404, "Software not found")

    full_path = os.path.join(config.UPLOAD_DIR, fw.path)

    if not os.path.exists(full_path):
        raise HTTPException(404, f"File '{fw.path}' not found on disk")

    return fw, full_path

def get_software_metadata(db: Session, software_id: int) -> schemas.SoftwareMetadata:
    fw, _ = get_software_full(db, software_id)
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', fw.name) if fw.name else fw.path
    download_name = f"{safe_name}.bin" if fw.name else fw.path

    return schemas.SoftwareMetadata(
        id=fw.id,
        name=fw.name,
        inner_name=fw.inner_name,
        filename_original=fw.path,
        filename_for_download=download_name
    )

def get_software_file_path(db: Session, software_id: int) -> str:
    _, file_path = get_software_full(db, software_id)
    return file_path

def get_software_file_info(db: Session, software_id: int) -> schemas.SoftwareFileLocation:
    _, file_path = get_software_full(db, software_id)
    return schemas.SoftwareFileLocation(
        full_path=file_path,
        size_bytes=os.path.getsize(file_path),
        exists=True
    )


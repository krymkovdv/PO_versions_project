from sqlalchemy.orm import Session
from . import models, schemas, config
from sqlalchemy import or_, cast, String, select, exists, and_
from fastapi import HTTPException, status, Depends, Form, File, UploadFile
from datetime import datetime
from typing import List
from .authorization import *
from .models import *
from datetime import timedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import re
import logging
import os
import uuid
from .config import UPLOAD_DIR

logger = logging.getLogger(__name__)

#---------АВТОРИЗАЦИЯ-------------
def get_users(db: Session):
    stmt = select(models.UserDB)
    result = db.execute(stmt).scalars().all()
    return result

def create_user(db: Session, user: schemas.UserCreate):
    # Проверка на дубликат username
    existing = db.query(models.UserDB).filter(models.UserDB.username == user.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")
    user_in = models.UserDB(
        username=user.username,
        password_hash=get_password_hash(user.password),
        role=user.role
    )
    db.add(user_in)
    try:
        db.commit()
        db.refresh(user_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="User already exists")
    return {"username": user_in.username, "role": user_in.role}

def delete_users(db: Session, id: int):
    user = db.query(models.UserDB).filter(models.UserDB.id == id).first()
    if user is None:
        return False
    db.delete(user)
    db.commit()
    return True

#----------БАЗОВЫЕ CRUDS----------
#Cruds for Tractor
def get_tractors(db: Session):
    stmt = select(models.Tractors)
    result = db.execute(stmt).scalars().all()
    return result

def create_tractor(db: Session, tractor: schemas.TractorsSchema):
    db_tractor = models.Tractors(
        model=tractor.model,
        vin=tractor.vin,
        oh_hour=tractor.oh_hour,
        last_activity=tractor.last_activity,
        assembly_date=tractor.assembly_date,
        region=tractor.region,
        consumer=tractor.consumer,
        serv_center=tractor.serv_center
    )
    db.add(db_tractor)
    db.commit()
    db.refresh(db_tractor)
    return db_tractor

def get_tractor_by_id(db: Session, id: int):
    return db.query(models.Tractors).filter(models.Tractors.id == id).first()

def delete_tractor(db: Session, id: int):
    tractor = db.query(models.Tractors).filter(models.Tractors.id == id).first()
    if tractor is None:
        return False
    db.delete(tractor)
    db.commit()
    return True

# CRUD для Component
def get_components(db: Session):
    stmt = select(models.Component)
    result = db.execute(stmt).scalars().all()
    return result

def get_component_by_id(db: Session, id: int):
    return db.query(models.Component).filter(models.Component.id == id).first()

def create_component(db: Session, component: schemas.ComponentSchema):
    db_component = models.Component(
        type=component.type,
        model=component.model,
        number_of_parts=component.number_of_parts,
        producer_comp=component.producer_comp
    )
    db.add(db_component)
    db.commit()
    db.refresh(db_component)
    return db_component

def delete_component(db: Session, id: int):
    component = db.query(models.Component).filter(models.Component.id == id).first()
    if component is None:
        return False
    db.delete(component)
    db.commit()
    return True

# CRUD для TelemetryComponents
def get_telemetry_components(db: Session):
    stmt = select(models.TelemetryComponents)
    result = db.execute(stmt).scalars().all()
    return result

def get_telemetry_component_by_id(db: Session, id: int):
    return db.query(models.TelemetryComponents).filter(models.TelemetryComponents.id == id).first()

def create_telemetry_component(db: Session, telemetry_component: schemas.TelemetryComponentSchema):
    db_telemetry_component = models.TelemetryComponents(
        tractor=telemetry_component.tractor,
        component=telemetry_component.component,
        time_rec=telemetry_component.time_rec,
        comp_ser_num=telemetry_component.comp_ser_num,
        mounting_date=telemetry_component.mounting_date,
        current_sw_version=telemetry_component.current_sw_version,
        recommend_sw_version=telemetry_component.recommend_sw_version
    )
    db.add(db_telemetry_component)
    db.commit()
    db.refresh(db_telemetry_component)
    return db_telemetry_component

def delete_telemetry_component(db: Session, id: int):
    telemetry_component = db.query(models.TelemetryComponents).filter(models.TelemetryComponents.id == id).first()
    if telemetry_component is None:
        return False
    db.delete(telemetry_component)
    db.commit()
    return True

# CRUD для Software
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

# CRUD для ComponentParts
def get_component_parts(db: Session):
    stmt = select(models.ComponentParts)
    result = db.execute(stmt).scalars().all()
    return result

def get_component_part_by_id(db: Session, id: int):
    return db.query(models.ComponentParts).filter(models.ComponentParts.id == id).first()

def create_component_part(db: Session, part: schemas.ComponentPartSchema):
    db_part = models.ComponentParts(
        component=part.component,
        part_type=part.part_type
    )
    db.add(db_part)
    db.commit()
    db.refresh(db_part)
    return db_part

def delete_component_part(db: Session, id: int):
    part = db.query(models.ComponentParts).filter(models.ComponentParts.id == id).first()
    if part is None:
        return False
    db.delete(part)
    db.commit()
    return True

# CRUD для Software2ComponentPart
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

#CRUD'ы для страницы 3
def get_component_by_filters(
    db: Session,
    trac_model: List[str],
    type_comp: List[str],
    model_comp: List[str]
):
    query = (
        db.query(
            models.Software.id,
            models.Software.path.label("download_link"),
            models.Software.name.label("producer_version"),
            models.Software.inner_name.label("inner_version"),
            models.Software.release_date,
            models.Software.id.label("id_Firmwares"),
            models.Component.type.label("type_component"),
            models.Component.model.label("model_component"),
            models.Software2ComponentPart.is_major.label("is_maj")
        )
        .select_from(models.Component)
        .outerjoin(models.TelemetryComponents, models.Component.id == models.TelemetryComponents.component)
        .outerjoin(models.Tractors, models.TelemetryComponents.tractor == models.Tractors.id)
        .outerjoin(models.ComponentParts, models.Component.id == models.ComponentParts.component)
        .outerjoin(models.Software, models.TelemetryComponents.current_sw_version == models.Software.id)
        .outerjoin(models.Software2ComponentPart, models.Software2ComponentPart.software_id == models.Software.id)
    )

    if trac_model:
        query = query.filter(models.Tractors.model.in_(trac_model))
    if type_comp:
        query = query.filter(models.Component.type.in_(type_comp))
    if model_comp:
        query = query.filter(models.Component.model.in_(model_comp))

    query = query.distinct()
    results = query.all()

    return [
        {
            "download_link": r.download_link,
            "type_component": r.type_component,
            "release_date": r.release_date.isoformat() if r.release_date else None,
            "inner_version": r.inner_version,
            "producer_version": r.producer_version,
            "is_maj": r.is_maj,
            "model_component": r.model_component,
            "id_Firmwares": r.id_Firmwares
        }
        for r in results
    ]

def search_components(db: Session, model_comp: str):
    query = (
        db.query(
            models.Software.id,
            models.Software.path.label("download_link"),
            models.Software.name.label("producer_version"),
            models.Software.inner_name.label("inner_version"),
            models.Software.release_date,
            models.Software.id.label("id_Firmwares"),
            models.Component.type.label("type_component"),
            models.Component.model.label("model_component"),
            models.Software2ComponentPart.is_major.label("is_maj")
        )
        .select_from(models.Component)
        .outerjoin(models.TelemetryComponents, models.Component.id == models.TelemetryComponents.component)
        .outerjoin(models.Tractors, models.TelemetryComponents.tractor == models.Tractors.id)
        .outerjoin(models.ComponentParts, models.Component.id == models.ComponentParts.component)
        .outerjoin(models.Software, models.TelemetryComponents.current_sw_version == models.Software.id)
        .outerjoin(models.Software2ComponentPart, models.Software2ComponentPart.software_id == models.Software.id)
    )

    if model_comp:
        user_input = model_comp.strip()
        if user_input:
            try:
                regex_pattern = schemas.wildcard_to_psql_regex(user_input)
                if not schemas.is_safe_regex(regex_pattern):
                    raise ValueError("Слишком сложный или потенциально опасный поисковый запрос")
                query = query.filter(models.Component.model.op('~*')(regex_pattern))
            except re.error as e:
                raise ValueError(f"Некорректный поисковый шаблон: {str(e)}")
            except Exception as e:
                raise ValueError(f"Ошибка при поиске: {str(e)}")

    query = query.distinct()
    results = query.all()

    return [
        {
            "download_link": r.download_link,
            "type_component": r.type_component,
            "release_date": r.release_date.isoformat() if r.release_date else None,
            "inner_version": r.inner_version,
            "producer_version": r.producer_version,
            "is_maj": r.is_maj,
            "model_component": r.model_component,
            "id_Firmwares": r.id_Firmwares
        }
        for r in results
    ]

# --- CRUD для Tractor Info (страница 4) ---

def get_tractors_by_filters(db: Session, filter: schemas.TractorFilter):
    # Подзапрос: найти тракторов, у которых есть нужда в major обновлении
    tractors_needing_major_update = select(models.Tractors.id).join(
        models.TelemetryComponents, models.Tractors.id == models.TelemetryComponents.tractor
    ).join(
        models.Component, models.TelemetryComponents.component == models.Component.id
    ).join(
        models.ComponentParts, models.Component.id == models.ComponentParts.component
    ).join(
        models.Software2ComponentPart, models.ComponentParts.id == models.Software2ComponentPart.component_part_id
    ).where(
        models.Software2ComponentPart.is_major == True,
        models.Software2ComponentPart.date_change_major.isnot(None),
        models.Software2ComponentPart.software_id != models.TelemetryComponents.current_sw_version
    ).distinct(models.Tractors.id).subquery()

    # Основной запрос: получить данные только для этих тракторов
    query = db.query(
        models.Tractors.vin,
        models.Tractors.model,
        models.Tractors.consumer,
        models.Tractors.assembly_date,
        models.Tractors.region,
        models.Tractors.oh_hour,
        models.Tractors.last_activity,
        models.Software.name,
        models.ComponentParts.id.label("componentPart_id"),
        models.Component.id.label("component_id"),
        models.Component.model.label("comp_model"),
        models.TelemetryComponents.recommend_sw_version,
        models.TelemetryComponents.current_sw_version,
        models.Software.description,
        models.Component.type
    ).select_from(
        models.Tractors
    ).join(
        models.TelemetryComponents, models.Tractors.id == models.TelemetryComponents.tractor
    ).join(
        models.Component, models.TelemetryComponents.component == models.Component.id
    ).join(
        models.ComponentParts, models.Component.id == models.ComponentParts.component
    ).outerjoin(
        models.Software, models.TelemetryComponents.current_sw_version == models.Software.id
    ).outerjoin(
        models.Software2ComponentPart, models.Software2ComponentPart.software_id == models.Software.id
    )

    if filter.is_major is not None:
        if filter.is_major:
            query = query.filter(models.Tractors.id.in_(select(tractors_needing_major_update.c.id)))
        else:
            query = query.filter(~models.Tractors.id.in_(select(tractors_needing_major_update.c.id)))

    if filter.query:
        q = filter.query.strip()
        if q:
            try:
                regex_pattern = schemas.wildcard_to_psql_regex(q)
                if not schemas.is_safe_regex(regex_pattern):
                    raise ValueError("Слишком сложный поисковый запрос")
                layout_regex = _similar_chars(regex_pattern)
                or_conditions = [
                    models.Tractors.vin.op('~*')(layout_regex),
                    models.Tractors.model.op('~*')(layout_regex),
                    models.Software.name.op('~*')(layout_regex),
                    models.Component.model.op('~*')(layout_regex),
                ]
                query = query.filter(or_(*or_conditions))
            except Exception as e:
                raise ValueError(f"Ошибка поиска: {str(e)}")

    if filter.date_assemle:
        try:
            if isinstance(filter.date_assemle, str):
                filter_date = datetime.strptime(filter.date_assemle, '%Y-%m-%d').date()
            else:
                filter_date = filter.date_assemle
            next_day = filter_date + timedelta(days=1)

            query = query.filter(
                models.Tractors.assembly_date >= filter_date,
                models.Tractors.assembly_date < next_day
            )
        except (ValueError, TypeError) as e:
            print(f"Ошибка преобразования даты: {e}")

    elif filter.date_start or filter.date_end:
        if filter.date_start and not filter.date_end:
            query = query.filter(models.Tractors.assembly_date >= filter.date_start)
            print(f"Фильтрация по дате ОТ: {filter.date_start}")

        elif filter.date_end and not filter.date_start:
            query = query.filter(models.Tractors.assembly_date <= filter.date_end)
            print(f"Фильтрация по дате ДО: {filter.date_end}")

        elif filter.date_start and filter.date_end:
            query = query.filter(
                models.Tractors.assembly_date >= filter.date_start,
                models.Tractors.assembly_date <= filter.date_end
            )
            print(f"Фильтрация по диапазону: {filter.date_start} - {filter.date_end}")

    query = query.distinct()
    results = query.all()

    return [
        {
            "vin": r.vin,
            "model": r.model,
            "consumer": r.consumer,
            "assembly_date": r.assembly_date.isoformat() if r.assembly_date else None,
            "region": r.region,
            "oh_hour": str(r.oh_hour) if r.oh_hour is not None else "",
            "last_activity": r.last_activity.isoformat() if r.last_activity else None,
            "sw_name": r.name,
            "componentParts_id": r.componentPart_id,
            "component_id": r.component_id,
            "comp_model": r.comp_model,
            "current_sw_version": r.current_sw_version,
            "description": r.description if r.description is not None else "",
            "recommend_sw_version": str(r.recommend_sw_version) if r.recommend_sw_version is not None else "",
            "component_type": r.type
        }
        for r in results
    ]

def search_tractors(db: Session, request: str):
    query = (
        db.query(
            models.Tractors.vin,
            models.Tractors.model,
            models.Tractors.consumer,
            models.Tractors.assembly_date,
            models.Tractors.region,
            models.Tractors.oh_hour,
            models.Tractors.last_activity,
            models.Software.name,
            models.ComponentParts.id.label("componentPart_id"),
            models.Component.id.label("component_id"),
            models.Component.model.label("comp_model"),
            models.TelemetryComponents.recommend_sw_version,
            models.TelemetryComponents.current_sw_version, 
            models.Software.description,
            models.Component.type
        )
        .select_from(models.Tractors)
        .outerjoin(models.TelemetryComponents, models.Tractors.id == models.TelemetryComponents.tractor)
        .outerjoin(models.Component, models.TelemetryComponents.component == models.Component.id)
        .outerjoin(models.ComponentParts, models.Component.id == models.ComponentParts.component)
        .outerjoin(models.Software, models.TelemetryComponents.current_sw_version == models.Software.id)
        .outerjoin(models.Software2ComponentPart, models.Software2ComponentPart.software_id == models.Software.id)
    )

    if request:
        q = request.strip()
        if q:
            try:
                regex_pattern = schemas.wildcard_to_psql_regex(q)
                if not schemas.is_safe_regex(regex_pattern):
                    raise ValueError("Слишком сложный поисковый запрос")
                layout_regex = _similar_chars(regex_pattern)
                or_conditions = [
                    models.Tractors.vin.op('~*')(layout_regex),
                    models.Tractors.model.op('~*')(layout_regex),
                    models.Software.name.op('~*')(layout_regex),
                    models.Component.model.op('~*')(layout_regex),
                ]
                query = query.filter(or_(*or_conditions))
            except Exception as e:
                raise ValueError(f"Ошибка поиска: {str(e)}")

    query = query.distinct()
    results = query.all()

    return [
        {
            "vin": r.vin,
            "model": r.model,
            "consumer": r.consumer,
            "assembly_date": r.assembly_date.isoformat() if r.assembly_date else None,
            "region": r.region,
            "oh_hour": str(r.oh_hour) if r.oh_hour is not None else "",
            "last_activity": r.last_activity.isoformat() if r.last_activity else None,
            "sw_name": r.name,
            "componentParts_id": r.componentPart_id,
            "component_id": r.component_id,
            "comp_model": r.comp_model,
            "current_sw_version": r.current_sw_version,
            "description": r.description if r.description is not None else "",
            "recommend_sw_version": str(r.recommend_sw_version) if r.recommend_sw_version is not None else "",
            "component_type": r.type
        }
        for r in results
    ]
def _similar_chars(regex_pattern: str) -> str:
    similar_chars = {
        'а': '[аa]', 'е': '[еe]', 'к': '[кk]', 'о': '[оo]', 'р': '[рp]',
        'с': '[сc]', 'у': '[уy]', 'х': '[хx]', 'м': '[мm]', 'н': '[нh]',
        'т': '[тt]', 'в': '[вb]',
        'a': '[aа]', 'e': '[eе]', 'k': '[kк]', 'o': '[oо]', 'p': '[pр]',
        'c': '[cс]', 'y': '[yу]', 'x': '[xх]', 'm': '[mм]', 'h': '[hн]',
        't': '[tт]', 'b': '[bв]'
    }

    result = []
    for char in regex_pattern:
        if char.lower() in similar_chars:
            if char.isupper():
                variants = similar_chars[char.lower()]
                result.append(f'({variants.upper()}|{variants})')
            else:
                result.append(similar_chars[char])
        else:
            result.append(char)
    return ''.join(result)

def get_tractor_by_vin(db: Session, vin: str):
    query = (
        db.query(
            models.Tractors.vin,
            models.Tractors.model,
            models.Tractors.consumer,
            models.Tractors.assembly_date,
            models.Tractors.region,
            models.Tractors.oh_hour,
            models.Tractors.last_activity,
            models.Software.name,
            models.Software.description,
            models.ComponentParts.id.label("componentPart_id"),
            models.Component.id.label("component_id"),
            models.Component.model.label("comp_model"),
            models.TelemetryComponents.current_sw_version,
            models.TelemetryComponents.recommend_sw_version, 
            models.Component.type
        )
        .select_from(models.Tractors)
        .outerjoin(models.TelemetryComponents, models.Tractors.id == models.TelemetryComponents.tractor)
        .outerjoin(models.Component, models.TelemetryComponents.component == models.Component.id)
        .outerjoin(models.ComponentParts, models.Component.id == models.ComponentParts.component)
        .outerjoin(models.Software, models.TelemetryComponents.current_sw_version == models.Software.id) 
    )

    query = query.filter(models.Tractors.vin == vin)
    query = query.distinct()
    results = query.all()

    return [
        {
            "vin": r.vin,
            "model": r.model,
            "consumer": r.consumer,
            "assembly_date": r.assembly_date.isoformat() if r.assembly_date else None,
            "region": r.region,
            "oh_hour": str(r.oh_hour) if r.oh_hour is not None else "",
            "last_activity": r.last_activity.isoformat() if r.last_activity else None,
            "sw_name": r.name,
            "description": r.description,
            "componentParts_id": r.componentPart_id,
            "component_id": r.component_id,
            "comp_model": r.comp_model,
            "current_sw_version": r.current_sw_version,
            "recommend_sw_version": str(r.recommend_sw_version) if r.recommend_sw_version is not None else "",
            "component_type": r.type
        }
        for r in results
    ]

def get_all_components_with_part(db: Session):
    stmt = (
        select(
            models.Component.id,
            models.Component.model,
            models.ComponentParts.part_type
        )
        .join(models.ComponentParts, models.Component.id == models.ComponentParts.component)
        .order_by(models.Component.model, models.ComponentParts.part_type)
    )

    result = db.execute(stmt).all()

    return [
        {
            "model(part)": f"{row.model} ({row.part_type})",
            "model": row.model,
            "part_type": row.part_type
        }
        for row in result
    ]

def secure_filename(filename: str) -> str:
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    return filename.strip("._")

def save_uploaded_file(file, filename: str) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_filename = f"{uuid.uuid4().hex}_{secure_filename(filename)}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

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
            path = os.path.join(UPLOAD_DIR, saved_filename)
            if os.path.exists(path):
                os.remove(path)
        raise

def get_software_full(db: Session, software_id: int):
    fw = db.query(models.Software).filter(
        models.Software.id == software_id
    ).first()

    if not fw:
        raise HTTPException(404, "Software not found")

    full_path = os.path.join(UPLOAD_DIR, fw.path)

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

def get_agg_by_trac_and_comp(db: Session, trac_model: List[str] = None, type_comp: List[str] = None):
    query = db.query(models.Component.model).distinct()

    if trac_model:
        query = query.join(models.TelemetryComponents, models.Component.id == models.TelemetryComponents.component)
        query = query.join(models.Tractors, models.TelemetryComponents.tractor == models.Tractors.id)
        query = query.filter(models.Tractors.model.in_(trac_model))
    if type_comp:
        query = query.filter(models.Component.type.in_(type_comp))

    results = query.all()
    return [r.model for r in results if r.model is not None]
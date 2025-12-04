from sqlalchemy.orm import Session
from . import models, schemas, config
from sqlalchemy import or_, cast, String, select
from fastapi import HTTPException, status, Depends, Form, File, UploadFile
from datetime import datetime
from typing import List
from .authorization import *
from .models import *
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import re
import logging
import os
import uuid


logger = logging.getLogger(__name__)
#---------АВТОРИЗАЦИЯ-------------
def get_users(db: Session):
    stmt = select(models.UserDB)
    result = db.execute(stmt).scalars().all()
    return result

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
        id = tractor.id,
        model=tractor.model,
        vin =tractor.vin,
        oh_hour = tractor.oh_hour,
        last_activity=tractor.last_activity,
        assembly_date=tractor.assembly_date,
        region = tractor.region,
        consumer = tractor.consumer,
        serv_center = tractor.serv_center
    )
    db.add(db_tractor)
    db.commit()
    db.refresh(db_tractor)
    return db_tractor

def get_tractor_by_terminal(db: Session, id: int):
    return db.query(models.Tractors).filter(models.Tractors.id == id).first()

def delete_tractor(db: Session, id: int):
    tractor = db.query(models.Tractors).filter(models.Tractors.id == id).first()
    if tractor is None:
        return False
    db.delete(tractor)
    db.commit()
    return True

# #Cruds for Component
def get_component(db: Session):
    stmt = select(models.Component)
    result = db.execute(stmt).scalars().all()
    return result

def get_component_by_terminal(db: Session, id: str):
    return db.query(models.Component).filter(models.Component.id == id).first()

def create_component(db: Session, component: schemas.ComponentSchema):
    db_component = models.Component(
        id = component.id,
        type = component.type,
        model = component.model,
        mounting_date = component.mounting_date,
        comp_ser_num = component.comp_ser_num,
        tractor_id = component.tractor_id,
        number_of_parts = component.number_of_parts,
        producer_comp = component.producer_comp
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

#CRUDs for TelemetryComponent
def get_telemetry_component(db: Session):
    stmt = select(models.TelemetryComponents)
    result = db.execute(stmt).scalars().all()
    return result

def get_telemetry_component_by_terminal(db: Session, id: str):
    return db.query(models.TelemetryComponents).filter(models.TelemetryComponents.id == id).first()

def create_telemetry_component(db: Session, telemetry_component: schemas.TelemetryComponentSchema):
    db_telemetry_component = models.TelemetryComponents(
        id= telemetry_component.id,
        software = telemetry_component.software,
        tractor = telemetry_component.tractor,
        component = telemetry_component.component,
        component_part_id = telemetry_component.component_part_id,
        time_rec = telemetry_component.time_rec
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

#CRUDs for Software
def download_software(db: Session, id: int):
    """
    Получить информацию о прошивке для скачивания
    """
    fw = db.query(models.Software).filter(models.Software.id == id).first()
    if not fw:
        return None
    return fw


def get_software(db: Session):
    stmt = select(models.Software)
    result = db.execute(stmt).scalars().all()
    return result

def get_software_by_terminal(db: Session, id: str):
    return db.query(models.Software).filter(models.Software.id == id).first()

def create_software(db: Session, software: schemas.SoftwareSchema):
    db_software = models.Software(
        id = software.id,
        path = software.path,
        name = software.name,
        inner_name = software.inner_name,
        release_date = software.release_date,
        description = software.description
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

# #CRUDs for ComponentsPart
def get_componentPart(db: Session):
    stmt = select(models.ComponentParts)
    result = db.execute(stmt).scalars().all()
    return result

def get_componentPart_by_terminal(db: Session, id: str):
    return db.query(models.ComponentParts).filter(models.ComponentParts.id == id).first()

def create_componentPart(db: Session, part: schemas.ComponentPartSchema):
        db_part = models.ComponentParts(
            id = part.id,
            component = part.component,
            part_number = part.part_number,
            part_type = part.part_type,
            current_sw_version = part.current_sw_version,
            recommend_sw_version = part.recommend_sw_version,
            is_major = part.is_major,
            not_recom_sw = part.not_recom,
            next_ver = part.next_ver
        )        
        db.add(db_part)
        db.commit()
        db.refresh(db_part)
        return db_part

def delete_componentPart(db: Session, id: int):
    component = db.query(models.ComponentParts).filter(models.ComponentParts.id == id).first()
    if component is None:
        return False
    db.delete(component)
    db.commit()
    return True

#CRUDs for Software2ComponentParts
def get_software_componentParts(db: Session):
    stmt = select(models.Software2ComponentPart)
    result = db.execute(stmt).scalars().all()
    return result

def get_software_componentsParts_by_terminal(db: Session, id: str):
    return db.query(models.Software2ComponentPart).filter(models.Software2ComponentPart.id == id).first()

def create_software_componentsParts(db: Session, software_components: schemas.SoftwareComponentsSchema):

    db_software_components = models.Software2ComponentPart(
        id = software_components.id,
        component_part_id = software_components.component_part_id,
        software_id = software_components.software_id,
        is_major = software_components.is_major,
        status = software_components.status,
        date_change = software_components.date_change,
        not_recom = software_components.not_recom,
        date_change_record = software_components.date_change_record
        )
    db.add(db_software_components)
    db.commit()
    db.refresh(db_software_components)
    return db_software_components

def delete_software_components(db: Session, id: int):
    db.delete(db.query(models.Software2ComponentPart).filter(models.Software2ComponentPart.id == id).first())
    db.commit()



#CRUD'ы для страницы 3
#ПО фильтрам Компоненты
def get_component_by_filters (db: Session, trac_model: List[str], type_comp: List[str], model_comp: str):
    query = db.query(models.Software.id, 
                    models.Software.path.label("download_link"),
                    models.Software.name.label("producer_version"),
                    models.Software.inner_name.label("inner_version"),
                    models.Software.release_date,
                    models.Software.id.label("id_Firmwares"),
                    models.Component.type.label("type_component"),
                    models.Component.model.label("model_component"),
                    models.Software2ComponentPart.is_major.label("is_maj")
                        ).select_from(models.Component)
    query = query.outerjoin(models.Tractors, models.Component.tractor_id == models.Tractors.id)
    query = query.outerjoin(models.ComponentParts, models.Component.id == models.ComponentParts.component)
    query = query.outerjoin(models.Software, models.ComponentParts.current_sw_version == models.Software.id)
    query = query.outerjoin(models.Software2ComponentPart, models.Software2ComponentPart.software_id == models.Software.id) 
    
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

#Глобальный поиск компонентов
def search_components(db: Session, model_comp: str):
    query = db.query(
        models.Software.id,
        models.Software.path.label("download_link"),
        models.Software.name.label("producer_version"),
        models.Software.inner_name.label("inner_version"),
        models.Software.release_date,
        models.Software.id.label("id_Firmwares"),
        models.Component.type.label("type_component"),
        models.Component.model.label("model_component"),
        models.Software2ComponentPart.is_major.label("is_maj")
    ).select_from(models.Component)

    query = query.outerjoin(models.Tractors, models.Component.tractor_id == models.Tractors.id)
    query = query.outerjoin(models.ComponentParts, models.Component.id == models.ComponentParts.component)
    query = query.outerjoin(models.Software, models.ComponentParts.current_sw_version == models.Software.id)
    query = query.outerjoin(models.Software2ComponentPart, models.Software2ComponentPart.software_id == models.Software.id)

    # 🔍 Глобальный поиск по model_component с поддержкой расширенных wildcards
    if model_comp:
        user_input = model_comp.strip()
        if user_input:
            try:
                # 🔁 Переводим wildcard → regex
                regex_pattern = schemas.wildcard_to_psql_regex(user_input)
                
                # 🔐 Проверяем безопасность
                if not schemas.is_safe_regex(regex_pattern):
                    raise ValueError("Слишком сложный или потенциально опасный поисковый запрос")
                
                # 🚀 Выполняем case-insensitive regex-поиск в PostgreSQL
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
#CRUD'ы для страницы 4
#ПО фильтрам Трактора
def get_tractors_by_filters(db: Session, filter:schemas.TractorFilter):
    query = db.query(models.Tractors.vin,
                     models.Tractors.model,
                     models.Tractors.consumer,
                     models.Tractors.assembly_date,
                     models.Tractors.region,
                     models.Tractors.oh_hour,
                     models.Tractors.last_activity,
                     models.Software.name,
                     models.ComponentParts.id.label("componentParts_id"),
                     models.Component.id.label("component_id"),
                     models.Component.model.label("comp_model"),
                     models.ComponentParts.recommend_sw_version,
                     models.Component.type.label("component_type")
                     ).select_from(models.Tractors)
    query = query.outerjoin(models.Component, models.Component.tractor_id == models.Tractors.id)
    query = query.outerjoin(models.ComponentParts, models.Component.id == models.ComponentParts.component)
    query = query.outerjoin(models.Software, models.ComponentParts.current_sw_version == models.Software.id)
    query = query.outerjoin(models.Software2ComponentPart, models.Software2ComponentPart.software_id == models.Software.id)

    
    if filter.trac_model:
        query = query.filter(models.Tractors.model.in_(filter.trac_model))
    if filter.status:
        query = query.filter(models.Software2ComponentPart.status.in_(filter.status))
    if filter.dealer:
        query = query.filter(models.Tractors.consumer == filter.dealer)
    if filter.date_assemle:
        query = query.filter(models.Tractors.assembly_date == filter.date_assemle)


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
            "componentParts_id": r.componentParts_id,
            "component_id": r.component_id,
            "comp_model": r.comp_model,
            "recommend_sw_version": str(r.recommend_sw_version) if r.recommend_sw_version is not None else "",
            "component_type": r.component_type
        }
        for r in results
    ]
     
#Глобальный поиск ТРАКТОРОВ
def search_tractors(db: Session, request: str):
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
        models.ComponentParts.recommend_sw_version,
        models.Component.type
    ).select_from(models.Tractors)

    query = query.outerjoin(models.Component, models.Component.tractor_id == models.Tractors.id)
    query = query.outerjoin(models.ComponentParts, models.Component.id == models.ComponentParts.component)
    query = query.outerjoin(models.Software, models.ComponentParts.current_sw_version == models.Software.id)
    query = query.outerjoin(models.Software2ComponentPart, models.Software2ComponentPart.software_id == models.Software.id)

    if request:
        q = request.strip()
        if q:
            try:
                # 🔁 Wildcard → regex
                regex_pattern = schemas.wildcard_to_psql_regex(q)
                
                # 🔐 Безопасность
                if not schemas.is_safe_regex(regex_pattern):
                    raise ValueError("Слишком сложный поисковый запрос")
                
                # 🚀 Используем ~* (case-insensitive regex в PostgreSQL)
                or_conditions = [
                    models.Tractors.vin.op('~*')(regex_pattern),
                    models.Tractors.model.op('~*')(regex_pattern),
                    models.Software.name.op('~*')(regex_pattern),
                    models.Component.model.op('~*')(regex_pattern),
                ]
                query = query.filter(or_(*or_conditions))
                
            except Exception as e:
                # Логируем, но не падаем — можно вернуть пустой результат или ошибку
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
            "recommend_sw_version": str(r.recommend_sw_version) if r.recommend_sw_version is not None else "",
            "component_type": r.type
        }
        for r in results
    ]


#для страницы с инфе про трактор
def get_tractor_by_vin(db: Session, vin: str):
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
        models.ComponentParts.current_sw_version,
        models.ComponentParts.recommend_sw_version,
        models.Component.type,
        models.Software.description
    ).select_from(models.Tractors)

    query = query.outerjoin(models.Component, models.Component.tractor_id == models.Tractors.id)
    query = query.outerjoin(models.ComponentParts, models.Component.id == models.ComponentParts.component)
    query = query.outerjoin(models.Software, models.ComponentParts.current_sw_version == models.Software.id)
    query = query.outerjoin(models.Software2ComponentPart, models.Software2ComponentPart.software_id == models.Software.id)

    query = query.filter(models.Tractors.vin == vin)

    query = query.distinct()
    results = query.all()

    return[
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
            "recommend_sw_version": str(r.recommend_sw_version) if r.recommend_sw_version is not None else "",
            "component_type": r.type,
            "description": r.description
        }
        for r in results
    ]



def secure_filename(filename: str) -> str:
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    return filename.strip("._")

def save_uploaded_file(file, filename: str) -> str:
    """Сохраняет файл из FastAPI UploadFile или bytes"""
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

def assign_software_to_components(
    db: Session,
    file: UploadFile,  # ← будем передавать UploadFile напрямую (потоково)
    software_data: schemas.AssignSoftwareRequest
) -> schemas.SoftwareResponse:

    try:
        # 1. Загружаем файл ПО
        saved_filename = save_uploaded_file(file, file.filename)
        
        # 2. Создаём запись в Software
        fw = models.Software(
            path=saved_filename,
            name=software_data.name,
            inner_name=software_data.inner_name,
            release_date=software_data.release_date,
            description=software_data.description
        )
        db.add(fw)
        db.flush()  # ← получаем fw.id, но не коммитим пока
        
        # 3. Для каждого компонента создаём связь
        for comp_models in software_data.component_models:
            # Проверяем, что компонент существует
            component = db.query(models.Component).filter(
                models.Component.model == comp_models
            ).first()
            if not component:
                raise HTTPException(404, f"Component {comp_models} not found")
            
            # Создаём ComponentParts для компонента (если не существует)
            # Предположим: у компонента одна часть (part_number = "default")
            part = db.query(models.ComponentParts).filter(
                models.ComponentParts.component == component.id,
                models.ComponentParts.part_number == software_data.part_number
            ).first()
            
            if not part:
                part = models.ComponentParts(
                    component=comp_models,
                    part_number= 0,
                    part_type=component.type,
                    current_sw_version=fw.id,  # сразу ставим как текущую
                    recommend_sw_version=fw.id,
                    is_major=True,
                    next_ver=""
                )
                db.add(part)
                db.flush()  
            
            link = models.Software2ComponentPart(
                component_part_id=part.id,
                software_id=fw.id,
                is_major=software_data.is_major,
                status='s',  
                date_change=datetime.utcnow().date(),
                date_change_record= None
            )
            db.add(link)
        
        # 4. Коммитим всё вместе
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
        # Удаляем файл при ошибке
        if 'saved_filename' in locals():
            path = os.path.join(config.UPLOAD_DIR, saved_filename)
            if os.path.exists(path):
                os.remove(path)
        raise

def get_software_full(db: Session, software_id: int) -> tuple[models.Software, str]:
    """
    Возвращает (модель Software, полный путь к файлу).
    Проверяет существование записи и файла.
    """
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

from sqlalchemy import func

def get_agg_by_trac_and_comp(db: Session, trac_model: str = None, type_comp: str = None):
    query = (
        db.query(models.Component.model)
        .select_from(models.Tractors)
        .join(models.Component, models.Component.tractor_id == models.Tractors.id)
        .distinct()
    )
    
    # Условное применение фильтров
    if trac_model:
        query = query.filter(models.Tractors.model == trac_model)
    if type_comp:
        query = query.filter(models.Component.type == type_comp)
    
    results = query.all()
    return [r.model for r in results if r.model is not None]
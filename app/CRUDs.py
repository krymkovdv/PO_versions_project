from sqlalchemy.orm import Session
from . import models, schemas, config
from sqlalchemy import or_, cast, String, select, func
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
from typing import List, Dict, Any


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

    #  Глобальный поиск по model_component с поддержкой расширенных wildcards
    if model_comp:
        user_input = model_comp.strip()
        if user_input:
            try:
                #  Переводим wildcard → regex
                regex_pattern = schemas.wildcard_to_psql_regex(user_input)
                
                #  Проверяем безопасность
                if not schemas.is_safe_regex(regex_pattern):
                    raise ValueError("Слишком сложный или потенциально опасный поисковый запрос")
                
                #  Выполняем case-insensitive regex-поиск в PostgreSQL
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
def get_tractors_by_filters(db: Session, filter: schemas.TractorFilter) -> List[Dict[str, Any]]:
    query = db.query(
        models.Tractors.vin,
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
        models.Component.type.label("component_type"),
        models.Software2ComponentPart.is_major.label("is_major")  # ВАЖНО: Добавьте это
    ).select_from(models.Tractors)
    
    query = query.outerjoin(models.Component, models.Component.tractor_id == models.Tractors.id)
    query = query.outerjoin(models.ComponentParts, models.Component.id == models.ComponentParts.component)
    query = query.outerjoin(models.Software, models.ComponentParts.current_sw_version == models.Software.id)
    query = query.outerjoin(models.Software2ComponentPart, models.Software2ComponentPart.software_id == models.Software.id)

    # Фильтрация по модели трактора
    if filter.trac_model:
        query = query.filter(models.Tractors.model.in_(filter.trac_model))

    # Фильтрация по статусу
    if filter.status:
        query = query.filter(models.Software2ComponentPart.status.in_(filter.status))

    # Фильтрация по дилеру (consumer)
    if filter.dealer:
        query = query.filter(models.Tractors.consumer == filter.dealer)

    if filter.is_major:
        query = query.filter(models.Software2ComponentPart.is_major == filter.is_major)
    # Фильтрация по дате сборки
    if filter.date_assemle:
        try:
            # Поддерживаем как строку, так и date (если Pydantic уже распарсил)
            if isinstance(filter.date_assemle, str):
                filter_date = datetime.strptime(filter.date_assemle, '%Y-%m-%d').date()
            else:
                filter_date = filter.date_assemle  # уже date объект

            # Используем timedelta для безопасного перехода к следующему дню
            next_day = filter_date + timedelta(days=1)

            query = query.filter(
                models.Tractors.assembly_date >= filter_date,
                models.Tractors.assembly_date < next_day
            )
        except (ValueError, TypeError) as e:
            print(f"Ошибка преобразования даты: {e}")
            # Опционально: можно игнорировать фильтр или бросать исключение

    elif filter.date_start or filter.date_end:
        if filter.date_start and not filter.date_end:
            query = query.filter(models.Tractors.assembly_date >= filter.date_end)
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


    # === ВАЖНО: distinct и выполнение запроса — вынесены НАРУЖУ ===
    query = query.distinct()
    results = query.all()

    # Преобразуем результаты в список словарей
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
            "component_type": r.component_type,
            "is_major": r.is_major
        }
        for r in results
    ]

def _similar_chars(regex_pattern: str) -> str:
    """
    Преобразует regex для поддержки визуально похожих букв в разных раскладках.
    Только для действительно похожих символов.
    """
    similar_chars = {
        'а': '[аa]',      # a
        'е': '[еe]',      # e
        'к': '[кk]',      # k
        'о': '[оo]',      # o
        'р': '[рp]',      # p
        'с': '[сc]',      # c
        'у': '[уy]',      # y
        'х': '[хx]',      # x
        'м': '[мm]',      # m
        'н': '[нh]',      # h
        'т': '[тt]',      # t
        'в': '[вb]',      # b
        
        # Английская -> Русская
        'a': '[aа]',
        'e': '[eе]',
        'k': '[kк]',
        'o': '[oо]',
        'p': '[pр]',
        'c': '[cс]',
        'y': '[yу]',
        'x': '[xх]',
        'm': '[mм]',
        'h': '[hн]',
        't': '[tт]',
        'b': '[bв]'
    }
    
    result = []
    for char in regex_pattern:
        if char.lower() in similar_chars:
            if char.isupper():
                # Для заглавных букв создаем варианты в обоих регистрах
                variants = similar_chars[char.lower()]
                result.append(f'({variants.upper()}|{variants})')
            else:
                result.append(similar_chars[char])
        else:
            result.append(char)
    
    return ''.join(result)               
    


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
        models.Software.description,
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
            "description": r.description,
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

def get_all_components_with_part(db: Session):
    stmt = (
        select(
            models.Component.id,
            models.Component.model,      
            models.ComponentParts.part_number 
        )
        .join(models.ComponentParts, models.Component.id == models.ComponentParts.component)
        .order_by(models.Component.model, models.ComponentParts.part_number)
    )
    
    result = db.execute(stmt).all()
    
    # Превращаем в список словарей или объектов
    return [
        {
            "model(part)": f"{row.model} ({row.part_number})",
            "model": row.model,                             
            "part_number": row.part_number
        }
        for row in result
    ]

def assign_software_to_components(
    db: Session,
    file: UploadFile,
    software_data: schemas.AssignSoftwareRequest
) -> schemas.SoftwareResponse:

    saved_filename = None
    try:
        # 1. Сохраняем файл ПО (один раз!)
        saved_filename = save_uploaded_file(file, file.filename)
        
        # 2. Создаём запись ПО
        fw = models.Software(
            path=saved_filename,
            name=software_data.name,
            inner_name=software_data.inner_name,
            release_date=software_data.release_date,
            description=software_data.description
        )
        db.add(fw)
        db.flush()  # получаем fw.id

        # 3. Проверяем соответствие длин списков
        n_models = len(software_data.component_models)
        n_parts = len(software_data.part_number)
        if n_models != n_parts:
            raise HTTPException(
                400, 
                f"Несоответствие: component_models ({n_models}) и part_number ({n_parts}) должны иметь одинаковую длину"
            )
        if n_models == 0:
            raise HTTPException(400, "Должен быть указан хотя бы один компонент")

        # 4. Обрабатываем каждую пару (model, part_number)
        for i in range(n_models):
            comp_model = software_data.component_models[i]
            part_num = software_data.part_number[i]

            # Находим компонент по модели
            component = db.query(models.Component).filter(
                models.Component.model == comp_model
            ).first()
            if not component:
                raise HTTPException(404, f"Component model '{comp_model}' not found")

            # Находим или создаём часть
            part = db.query(models.ComponentParts).filter(
                models.ComponentParts.component == component.id,
                models.ComponentParts.part_number == part_num
            ).first()
            
            if not part:
                part = models.ComponentParts(
                    component=component.id,
                    part_number=part_num,
                    part_type=component.type,
                    current_sw_version=fw.id,
                    recommend_sw_version=fw.id,
                    is_major=software_data.is_major,
                    next_ver=""
                )
                db.add(part)
                db.flush()  # получаем part.id

            # Создаём связь ПО ↔ часть компонента
            link = models.Software2ComponentPart(
                component_part_id=part.id,
                software_id=fw.id,
                is_major=software_data.is_major,
                status='s',
                date_change=datetime.utcnow().date(),
            )
            db.add(link)

        # 5. Коммитим всё вместе
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

def get_software_full(db: Session, software_id: int) -> tuple[models.Software, str]:
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

def get_agg_by_trac_and_comp(db: Session, trac_model: List[str] = None, type_comp: List[str] = None):
    query = (
        db.query(models.Component.model)

        # .join(models.Component, models.Component.tractor_id == models.Tractors.id)
        .distinct()
    )
    
    # Условное применение фильтров
    if trac_model:
        query = query.join(models.Tractors, models.Component.tractor_id == models.Tractors.id)
        query = query.filter(models.Tractors.model.in_(trac_model))
    if type_comp:
        query = query.filter(models.Component.type.in_(type_comp))
    
    results = query.all()
    return [r.model for r in results if r.model is not None]

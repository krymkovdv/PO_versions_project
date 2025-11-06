from sqlalchemy.orm import Session
from . import models, schemas  
from sqlalchemy import or_, cast, String, select
from fastapi import HTTPException
from datetime import datetime
from typing import List

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
            not_recom_sw = part.not_recom_sw,
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
# def get_component_by_filters (db: Session, trac_model: List[str], type_comp: List[str], model_comp: str):
#     query = db.query(models.Software.id, 
#                         models.Software.name, 
#                         models.Software.release_date, 
#                         models.Software.path, 
#                         models.Software.inner_name,
#                         models.Component.type,
#                         models.Component.model,
#                         models.Software2ComponentPart.is_major, 
#                         models.Component.type, 
#                         models.Component.model
#                         ).select_from(models.Component)
#     query = query.join(models.Tractors, models.Component.tractor_id == models.Tractors.id)
#     query = query.join(models.ComponentParts, models.Component.id == models.ComponentParts.component)
#     query = query.join(models.Software, models.ComponentParts.current_sw_version == models.Software.id)
#     query = query.join(models.Software2ComponentPart, models.Software2ComponentPart.software_id == models.Software.id) 
    
#     if trac_model:
#         query = query.filter(models.Tractors.model.in_(trac_model))
#     if type_comp:
#         query = query.filter(models.Component.type.in_(type_comp))
#     if model_comp:
#         query = query.filter(models.Component.model == model_comp)

#     query = query.order_by(models.Software.release_date.desc())

#     results = query.all()

#     return [
#         {
#             "download_link": r.path,
#             "type_component": r.type_component,
#             "release_date": r.release_date.isoformat() if r.release_date else None,
#             "inner_version": r.inner_version,
#             "producer_version": r.producer_version,
#             "is_maj": r.is_maj,
#             "model_component": r.model_component,
#             "id_Firmwares": r.id_Firmwares,
#         }
#         for r in results
#     ]

#Глобальный поиск компонентов




#CRUD'ы для страницы 4

#ПО фильтрам Трактора

#Глобальный поиск тракторов

#ОСТАЛЬНЫК ХЗ


# ----------------- СТАРЫЕ КРУДЫ ----------------
# #Большой поиск по фильтрам
# def get_tractor_software(db: Session, filters: schemas.TractorFilter):
#     # Начинаем с Tractors и джойним всё нужное
#     query = (
#         db.query(models.Tractors)
#         .join(models.TelemetryComponents, models.Tractors.id == models.TelemetryComponents.tractor)
#         .join(models.Component, models.TelemetryComponents.component == models.Component.id)
#         .join(models.SoftwareComponent, models.SoftwareComponent.component_id == models.Component.id)
#         .join(models.Software, models.SoftwareComponent.software_id == models.Software.id)
#     )

#     # 1. Фильтр по моделям трактора
#     if filters.models:
#         query = query.filter(models.Tractors.model.in_(filters.models))

#     # 2. Фильтр по дате сборки
#     if filters.release_date_from:
#         dt_from = datetime.fromisoformat(filters.release_date_from)
#         query = query.filter(models.Tractors.assembly_date >= dt_from)
#     if filters.release_date_to:
#         dt_to = datetime.fromisoformat(filters.release_date_to)
#         query = query.filter(models.Tractors.assembly_date <= dt_to)

#     # 3. Фильтр по is_major (MAJ/MIN)
#     if filters.requires_maj and filters.requires_min:
#         # Оба True — логически странно, но можно игнорировать или вернуть пусто
#         return []
#     elif filters.requires_maj:
#         query = query.filter(models.SoftwareComponent.is_major == True)
#     elif filters.requires_min:
#         query = query.filter(models.SoftwareComponent.is_major == False)

#     tractors = query.all()

#     result = []
#     for tractor in tractors:
#         components = []

#         # Проходим по telemetry → component → software_component → software
#         for tel in tractor.tel_trac:
#             comp = tel.components  # ← relationship, не foreign key!
#             if comp is None:
#                 continue  

#         for sc in comp.software_links:
#             software = sc.software
#                 # Собираем данные прошивки
#             fw_info = schemas.FirmwareInfo(
#                 inner_version=software.inner_name or "",
#                 producer_version=software.name,
#                 download_link=software.path,
#                 release_date=software.release_date.isoformat() if software.release_date else None,
#                 maj_to=None,  # у вас нет этих полей — можно убрать или добавить в модель
#                 min_to=None,
#             )

#             comp_info = schemas.ComponentInfo(
#                 type_component=comp.type,
#                 model_component=comp.model,
#                 year_component=comp.date_create.isoformat() if comp.date_create else None,
#                 current_version_id=software.id,
#                 is_maj=sc.is_major,
#                 firmware=fw_info,
#             )
#             components.append(comp_info)

#         resp = schemas.TractorSoftwareResponse(
#             vin=tractor.vin,
#             model=tractor.model,
#             assembly_date=tractor.assembly_date.isoformat() if tractor.assembly_date else None,
#             components=components,
#         )
#         result.append(resp)

#     return result


# # Дополнительные CRUD
# def get_tractor_component_by_vin(vin: str,db: Session):
#     if not vin:
#         raise HTTPException(status_code=400, detail="vin is required")

#     # Находим трактор по VIN
#     tractor = db.query(models.Tractors).filter(models.Tractors.vin == vin).first()
#     if not tractor:
#         raise HTTPException(status_code=404, detail="Tractor not found")

#     # Находим все телеметрические записи для этого трактора
#     tel_components = db.query(models.TelemetryComponents).filter(
#         models.TelemetryComponents.tractor == tractor.id
#     ).all()

#     info = []
#     for tel in tel_components:
#         # Получаем компонент (один, так как tel.component — FK)
#         comp = db.query(models.Component).filter(models.Component.id == tel.component).first()
#         if not comp:
#             continue  # или raise, если компонент обязан существовать

#         # Получаем связь "компонент-софт" (предполагаем одну активную запись)
#         soft_link = db.query(models.SoftwareComponent).filter(
#             models.SoftwareComponent.component_id == comp.id,
#             models.SoftwareComponent.status == 's'  # только стабильные версии
#         ).first()

#         if not soft_link:
#             # Можно пропустить или использовать заглушку
#             continue

#         # Получаем саму прошивку
#         software = db.query(models.Software).filter(
#             models.Software.id == soft_link.software_id
#         ).first()
#         if not software:
#             continue

#         # Собираем данные прошивки
#         firmware_info = schemas.FirmwareInfo(
#             inner_version=software.inner_name or "",
#             producer_version=software.name,
#             download_link=software.path,
#             release_date=software.release_date.isoformat() if software.release_date else None
#         )

#         # Собираем информацию о компоненте
#         comp_info = schemas.ComponentInfo(
#             type_component=comp.type,
#             model_component=comp.model,
#             year_component=comp.date_create.isoformat() if comp.date_create else None,
#             current_version_id=soft_link.software_id,
#             is_maj=soft_link.is_major,
#             firmware=firmware_info,
#         )
#         info.append(comp_info)

#     # Возвращаем ответ в формате TractorSoftwareResponse
#     response = schemas.TractorSoftwareResponse(
#         vin=tractor.vin,
#         model=tractor.model,
#         assembly_date=tractor.assembly_date.isoformat() if tractor.assembly_date else None,
#         components=info
#     )
#     return response


# def get_component_version_by_types(db: Session, type_comps: List[str]):
#     results = (
#         db.query(
#             models.Software.path,
#             models.Software.release_date,
#             models.Software.inner_name,
#             models.Software.name,
#             models.Software.id,
#             models.Component.type,
#             models.Component.model,
#             models.SoftwareComponent.is_major
#         )
#         .select_from(models.SoftwareComponent)
#         .join(models.Component, models.SoftwareComponent.component_id == models.Component.id)
#         .join(models.Software, models.SoftwareComponent.software_id == models.Software.id)
#         .filter(models.Component.type.in_(type_comps))
#         .order_by(models.Software.release_date.desc())
#         .all()
#     )

#     if results:
#         return [
#             {
#                 "download_link": r.path,
#                 "type_component": r.type,
#                 "release_date": r.release_date,
#                 "inner_version": r.inner_name,
#                 "producer_version": r.name,
#                 "is_maj": r.is_major,
#                 "model_component": r.model,
#                 "id_Firmwares": r.id
#             }
#             for r in results
#         ]
#     else:
#         return []

# def get_all_components(db: Session):
#     results = (db.query(
#                 models.Software.path,
#                 models.Software.release_date,
#                 models.Software.inner_name,
#                 models.Software.name,
#                 models.Software.id,
#                 models.Component.type,
#                 models.Component.model,
#                 models.SoftwareComponent.is_major
#             )
#             .select_from(models.SoftwareComponent)
#             .join(models.Component, models.SoftwareComponent.component_id == models.Component.id)
#             .join(models.Software, models.SoftwareComponent.software_id == models.Software.id)
#             .order_by(models.Software.release_date.desc())
#             .all()) 
    
#     if results:
#         return [
#             {
#                 "download_link": result.path,
#                 "type_component": result.type,
#                 "release_date": result.release_date,
#                 "inner_name": result.inner_name,
#                 "name": result.name,
#                 "is_major": result.is_major,
#                 "model": result.model,
#                 "id": result.id
#             }
#             for result in results  
#         ]
#     else:
#         return None


# def get_component_version_by_models(db: Session, model_comp: str):
#     results = (db.query(
#                 models.Software.path,
#                 models.Software.release_date,
#                 models.Software.inner_name,
#                 models.Software.name,
#                 models.Software.id,
#                 models.Component.type,
#                 models.Component.model,
#                 models.SoftwareComponent.is_major
#             )
#             .select_from(models.SoftwareComponent)
#             .join(models.Component, models.SoftwareComponent.component_id == models.Component.id)
#             .join(models.Software, models.SoftwareComponent.software_id == models.Software.id)
#             .filter(models.Component.model == model_comp)
#             .order_by(models.Software.release_date.desc())
#             .all()) 
    
#     if results:
#         return [
#             {
#                 "download_link": result.path,
#                 "type_component": result.type, 
#                 "release_date": result.release_date,
#                 "inner_version": result.inner_name,
#                 "producer_version": result.name,
#                 "is_maj": result.is_major,
#                 "model_component": result.model,
#                 "id_Firmwares": result.id
#             }
#             for result in results  
#         ]
#     else:
#         return None
    
# def get_component_version_by_type_models(db: Session, model_comp: str, type_comp: str):
#     results = (db.query(
#                 models.Software.path,
#                 models.Software.release_date,
#                 models.Software.inner_name,
#                 models.Software.name,
#                 models.Software.id,
#                 models.Component.type,
#                 models.Component.model,
#                 models.SoftwareComponent.is_major
#             )
#             .select_from(models.SoftwareComponent)
#             .join(models.Component, models.SoftwareComponent.component_id == models.Component.id)
#             .join(models.Software, models.SoftwareComponent.software_id == models.Software.id)
#             .filter(models.Component.model == model_comp,
#                     models.Component.type == type_comp)
#             .order_by(models.Software.release_date.desc())
#             .all()) 
    
#     if results:
#         return [
#             {
#                 "download_link": result.path,
#                 "type_component": result.type, 
#                 "release_date": result.release_date,
#                 "inner_version": result.inner_name,
#                 "producer_version": result.name,
#                 "is_maj": result.is_major,
#                 "model_component": result.model,
#                 "id_Firmwares": result.id
#             }
#             for result in results  
#         ]
#     else:
#         return None
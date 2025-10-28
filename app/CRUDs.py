from sqlalchemy.orm import Session
from . import models, schemas  
from sqlalchemy import or_, cast, String, select
from fastapi import HTTPException
from datetime import datetime

#Cruds for Tractor
def smart_search_tractors(db: Session, query: str):
    """
    Умный поиск по VIN, модели, серийному номеру, последней активности
    """
    search = f"%{query}%"
    tractors = db.query(models.Tractors).filter(
        or_(
            cast(models.Tractors.id, String).like(search),
            models.Tractors.model.like(search),
            models.Tractors.vin.like(search),
            cast(models.Tractors.last_activity, String).like(search),      
            cast(models.Tractors.assembly_date, String).like(search)  
        )
    ).all()
    return tractors

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
        assembly_date=tractor.assembly_date
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
        date_create = component.date_create
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
        time_rec = telemetry_component.time_rec,
        serial_number = telemetry_component.serial_number
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
        prev_version = software.prev_version,
        next_version = software.next_version,
        release_date = software.release_date
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

# #CRUDs for Relations
def get_relations(db: Session):
    stmt = select(models.Relations)
    result = db.execute(stmt).scalars().all()
    return result

def get_relations_by_terminal(db: Session, id: str):
    return db.query(models.Relations).filter(models.Relations.id == id).first()

def create_relations(db: Session, relations: schemas.RelationSchema):
        if relations.software1 == relations.software2:
            raise HTTPException(status_code=400, detail="Software1 cant be equal to Software2")

        db_relations = models.Relations(
            id = relations.id,
            software1 = relations.software1,
            software2 = relations.software2
        )        
        db.add(db_relations)
        db.commit()
        db.refresh(db_relations)
        return db_relations

def delete_relations(db: Session, id: int):
    relations = db.query(models.Relations).filter(models.Relations.id == id).first()
    if relations is None:
        return False
    db.delete(relations)
    db.commit()
    return True

#CRUDs for SoftwareComponents
def get_software_components(db: Session):
    stmt = select(models.SoftwareComponent)
    result = db.execute(stmt).scalars().all()
    return result

def get_software_components_by_terminal(db: Session, id: str):
    return db.query(models.SoftwareComponent).filter(models.SoftwareComponent.id == id).first()

def create_software_components(db: Session, software_components: schemas.SoftwareComponentsSchema):

    db_software_components = models.SoftwareComponent(
        id = software_components.id,
        component_id = software_components.component_id,
        software_id = software_components.software_id,
        is_major = software_components.is_major,
        status = software_components.status,
        date_change = software_components.date_change)
    db.add(db_software_components)
    db.commit()
    db.refresh(db_software_components)
    return db_software_components

def delete_software_components(db: Session, id: int):
    db.delete(db.query(models.SoftwareComponent).filter(models.SoftwareComponent.id == id).first())
    db.commit()


# #Большой поиск по фильтрам(надо сделать)
def get_tractor_software(db: Session, filters: schemas.TractorFilter):
    # Начинаем с Tractors и джойним всё нужное
    query = (
        db.query(models.Tractors)
        .join(models.TelemetryComponents, models.Tractors.id == models.TelemetryComponents.tractor)
        .join(models.Component, models.TelemetryComponents.component == models.Component.id)
        .join(models.SoftwareComponent, models.SoftwareComponent.component_id == models.Component.id)
        .join(models.Software, models.SoftwareComponent.software_id == models.Software.id)
    )

    # 1. Фильтр по моделям трактора
    if filters.models:
        query = query.filter(models.Tractors.model.in_(filters.models))

    # 2. Фильтр по дате сборки
    if filters.release_date_from:
        dt_from = datetime.fromisoformat(filters.release_date_from)
        query = query.filter(models.Tractors.assembly_date >= dt_from)
    if filters.release_date_to:
        dt_to = datetime.fromisoformat(filters.release_date_to)
        query = query.filter(models.Tractors.assembly_date <= dt_to)

    # 3. Фильтр по is_major (MAJ/MIN)
    if filters.requires_maj and filters.requires_min:
        # Оба True — логически странно, но можно игнорировать или вернуть пусто
        return []
    elif filters.requires_maj:
        query = query.filter(models.SoftwareComponent.is_major == True)
    elif filters.requires_min:
        query = query.filter(models.SoftwareComponent.is_major == False)

    tractors = query.all()

    result = []
    for tractor in tractors:
        components = []

        # Проходим по telemetry → component → software_component → software
        for tel in tractor.tel_trac:
            comp = tel.components  # ← relationship, не foreign key!
            if comp is None:
                continue  
            
        for sc in comp.software_links:
            software = sc.software
                # Собираем данные прошивки
            fw_info = schemas.FirmwareInfo(
                inner_version=software.inner_name or "",
                producer_version=software.name,
                download_link=software.path,
                release_date=software.release_date.isoformat() if software.release_date else None,
                maj_to=None,  # у вас нет этих полей — можно убрать или добавить в модель
                min_to=None,
            )

            comp_info = schemas.ComponentInfo(
                type_component=comp.type,
                model_component=comp.model,
                year_component=comp.date_create.isoformat() if comp.date_create else None,
                current_version_id=software.id,
                is_maj=sc.is_major,
                firmware=fw_info,
            )
            components.append(comp_info)

        resp = schemas.TractorSoftwareResponse(
            vin=tractor.vin,
            model=tractor.model,
            assembly_date=tractor.assembly_date.isoformat() if tractor.assembly_date else None,
            components=components,
        )
        result.append(resp)

    return result
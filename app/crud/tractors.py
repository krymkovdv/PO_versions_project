from sqlalchemy.orm import Session
from .. import models, schemas
from sqlalchemy import select
import logging
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from typing import List

logger = logging.getLogger(__name__)

def get_tractors(db: Session):
    stmt = select(models.Tractor)
    result = db.execute(stmt).scalars().all()
    return result

def create_tractor(db: Session, tractor: schemas.TractorsSchema):
    db_tractor = models.Tractor(
        model=tractor.model,
        vin=tractor.vin,
        oh_hour=tractor.oh_hour,
        last_activity=tractor.last_activity,
        assembly_date=tractor.assembly_date,
        region=tractor.region,
        consumer=tractor.consumer,
        dealer=tractor.dealer
    )
    db.add(db_tractor)
    db.commit()
    db.refresh(db_tractor)
    return db_tractor

def get_tractor_by_id(db: Session, id: int):
    return db.query(models.Tractor).filter(models.Tractor.id == id).first()

def delete_tractor(db: Session, id: int):
    tractor = db.query(models.Tractor).filter(models.Tractor.id == id).first()
    if tractor is None:
        return False
    db.delete(tractor)
    db.commit()
    return True

def update_tractor(db: Session, vin: str, tractor_update: schemas.TractorUpdate):
    db_tractor = db.query(models.Tractor).filter(models.Tractor.vin == vin).first()
    if not db_tractor:
        raise HTTPException(status_code=404, detail="Tractor not found")
    for field, value in tractor_update.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(db_tractor, field, value)
    try:
        db.commit()
        db.refresh(db_tractor)
        return db_tractor
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Update failed due to integrity constraint")
    
def get_tractor_models(
    db: Session,
    component_types: List[str] = None,
    component_models: List[str] = None,
    component_producers: List[str] = None,
    software_status: List[str] = None
):
    """
    Получает уникальные модели тракторов, связанные с компонентами/ПО.
    Возвращает список словарей: [{'model': 'K-7'}, ...]
    """
    query = db.query(
        models.Tractor.model
    ).distinct()
    
    joined_tractor_link = False
    joined_software_link = False
    joined_software = False
    joined_component = False
    
    if component_types:
        if not joined_tractor_link:
            query = query.join(
                models.Tractor_Software_And_Component_Link,
                models.Tractor.id == models.Tractor_Software_And_Component_Link.tractor_id
            )
            joined_tractor_link = True
        if not joined_software_link:
            query = query.join(
                models.Software_Component_Link,
                models.Tractor_Software_And_Component_Link.soft_comp_link_id == models.Software_Component_Link.id
            )
            joined_software_link = True
        if not joined_component:
            query = query.join(
                models.Component,
                models.Software_Component_Link.component_id == models.Component.id
            )
            joined_component = True
        query = query.filter(models.Component.type.in_(component_types))

    if component_models:
        if not joined_component:
            if not joined_software_link:
                query = query.join(
                    models.Software_Component_Link,
                    models.Tractor.id == models.Tractor_Software_And_Component_Link.tractor_id
                )
                joined_software_link = True
            query = query.join(
                models.Component,
                models.Software_Component_Link.component_id == models.Component.id
            )
            joined_component = True
        query = query.filter(models.Component.name.in_(component_models))

    if component_producers:
        if not joined_component:
            if not joined_software_link:
                query = query.join(
                    models.Software_Component_Link,
                    models.Tractor.id == models.Tractor_Software_And_Component_Link.tractor_id
                )
                joined_software_link = True
            query = query.join(
                models.Component,
                models.Software_Component_Link.component_id == models.Component.id
            )
            joined_component = True
        query = query.filter(models.Component.producer.in_(component_producers))
    
    if software_status:
        if not joined_software_link:
            query = query.join(
                models.Software_Component_Link,
                models.Tractor.id == models.Tractor_Software_And_Component_Link.tractor_id
            )
            joined_software_link = True
        query = query.join(
            models.Software,
            models.Software_Component_Link.software_id == models.Software.id
        )
        query = query.filter(models.Software.status.in_(software_status))
    
    results = query.all()
    
    return [
        {"model": r.model} 
        for r in results 
        if r.model is not None
    ]
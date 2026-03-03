from sqlalchemy.orm import Session
from .. import models, schemas
from sqlalchemy import select
from typing import List
import logging
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

def get_components(db: Session):
    stmt = select(models.Component)
    result = db.execute(stmt).scalars().all()
    return result

def get_component_by_id(db: Session, id: int):
    return db.query(models.Component).filter(models.Component.id == id).first()

def create_component(db: Session, component: schemas.ComponentSchema):
    db_component = models.Component(
        type=component.type,
        name=component.name,
        producer=component.producer
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

def update_component(db: Session, component_id: int, component_update: schemas.ComponentUpdate):
    db_comp = db.query(models.Component).filter(models.Component.id == component_id).first()
    if not db_comp:
        raise HTTPException(status_code=404, detail="Component not found")
    for field, value in component_update.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(db_comp, field, value)
    try:
        db.commit()
        db.refresh(db_comp)
        return db_comp
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Update failed due to integrity constraint")

def get_agg_by_trac_and_comp(db: Session, trac_model: List[str] = None, type_comp: List[str] = None, producers: List[str] = None, status: List[str] = None):
    query = db.query(models.Component.model).distinct()
# producer dobavil
    if trac_model:
        query = query.join(models.TelemetryComponents, models.Component.id == models.TelemetryComponents.component)
        query = query.join(models.Tractors, models.TelemetryComponents.tractor == models.Tractors.id)
        query = query.filter(models.Tractors.model.in_(trac_model))
    if type_comp:
        query = query.filter(models.Component.type.in_(type_comp))
        # 
    if producers:
        query = query.filter(models.Component.producer_comp.in_(producers))
    if status:
        query = query.join(models.Component.parts).join(models.ComponentParts.software_link)
        query = query.filter(models.Software2ComponentPart.status.in_(status))
# 
    results = query.all()
    return [r.model for r in results if r.model is not None]    



from sqlalchemy.orm import Session
from .. import models, schemas
from sqlalchemy import select
from typing import List
import logging

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
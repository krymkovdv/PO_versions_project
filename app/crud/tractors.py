from sqlalchemy.orm import Session
from .. import models, schemas
from sqlalchemy import select
import logging
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException


logger = logging.getLogger(__name__)

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

def update_tractor(db: Session, vin: str, tractor_update: schemas.TractorUpdate):
    db_tractor = db.query(models.Tractors).filter(models.Tractors.vin == vin).first()
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
from sqlalchemy.orm import Session
from .. import models, schemas
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

def get_telemetry_components(db: Session):
    stmt = select(models.TelemetryComponents)
    result = db.execute(stmt).scalars().all()
    return result

def get_telemetry_component_by_id(db: Session, id: int):
    return db.query(models.TelemetryComponents).filter(models.TelemetryComponents.id == id).first()

def create_telemetry_component(db: Session, telemetry_component: schemas.TelemetryComponentSchema):

    current_sw = telemetry_component.current_sw_version
    if current_sw == 0:
        current_sw = None
        logger.warning(f"current_sw_version=0 преобразован в None")
    
    recommend_sw = telemetry_component.recommend_sw_version
    if recommend_sw == 0:
        recommend_sw = None
        logger.warning(f"recommend_sw_version=0 преобразован в None")


    db_telemetry_component = models.TelemetryComponents(
        tractor=telemetry_component.tractor,
        component=telemetry_component.component,
        time_rec=telemetry_component.time_rec,
        comp_ser_num=telemetry_component.comp_ser_num,
        mounting_date=telemetry_component.mounting_date,
        current_sw_version=current_sw,
        recommend_sw_version=recommend_sw
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
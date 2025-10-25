from sqlalchemy.orm import Session
from datetime import datetime
from . import models, schemas
from sqlalchemy import and_, or_, func, select
from sqlalchemy import cast, String


#Cruds for Tractor
def smart_search_tractors(db: Session, query: str):
    """
    Умный поиск по VIN, модели, серийному номеру, последней активности
    """
    search = f"%{query}%"
    tractors = db.query(models.Tractors).filter(
        or_(
            cast(models.Tractors.terminal_id, String).like(search),
            models.Tractors.model.like(search),
            models.Tractors.vin.like(search),
            models.Tractors.last_activity.like(search)
        )
    ).all()

    return tractors
def get_tractor(db: Session):
    stmt = select(models.Tractors)
    result = db.execute(stmt).scalars().all()
    return result

def create_tractor(db: Session, tractor: schemas.TractorsSchema):
    db_tractor = models.Tractors(
        tractor_id = tractor.id,
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

def get_tractor_by_terminal(db: Session, id: str):
    return db.query(models.Tractors).filter(models.Tractors.id == id).first()

def delete_tractor(db: Session, id: int):
    tractor = db.query(models.Tractors).filter(models.Tractors.id == id).first()
    if tractor is None:
        return False
    db.delete(tractor)
    db.commit()
    return True


# #Cruds for TractorComponent
# def get_tractor_component_by_terminal(db: Session, row_id: str):
#     return db.query(models.TractorComponent).filter(models.TractorComponent.row_id == row_id).first()

# def create_tractor_component(db: Session, tractor_component: schemas.TractorsComponentSchema):
#     db_tractor_component = models.TractorComponent(
#         row_id = tractor_component.row_id,
#         time_comp = tractor_component.time_comp,
#         tractor= tractor_component.tractor,
#         comp_id = tractor_component.comp_id
#     )
#     db.add(db_tractor_component)
#     db.commit()
#     db.refresh(db_tractor_component)
#     return db_tractor_component

# def delete_tractor_component(db: Session, tractor_component_row_id: int):
#     tractor_component = db.query(models.TractorComponent).filter(models.TractorComponent.row_id == tractor_component_row_id).first()
#     if tractor_component is None:
#         return False
#     db.delete(tractor_component)
#     db.commit()
#     return True

# #CRUDs for TelemetryComponent
# def get_telemetry_component_by_terminal(db: Session, telemetry_id: str):
#     return db.query(models.TelemetryComponents).filter(models.TelemetryComponents.telemetry_id == telemetry_id).first()

# def create_telemetry_component(db: Session, telemetry_component: schemas.TelemetryComponentSchema):
#     db_telemetry_component = models.TelemetryComponents(
#         telemetry_id= telemetry_component.telemetry_id,
#         current_version = telemetry_component.current_version,
#         true_comp = telemetry_component.true_comp,
#         is_maj = telemetry_component.is_maj
#     )
#     db.add(db_telemetry_component)
#     db.commit()
#     db.refresh(db_telemetry_component)
#     return db_telemetry_component

# def delete_telemetry_component(db: Session, telemetry_component_telemetry_id: int):
#     telemetry_component = db.query(models.TelemetryComponents).filter(models.TelemetryComponents.telemetry_id == telemetry_component_telemetry_id).first()
#     if telemetry_component is None:
#         return False
#     db.delete(telemetry_component)
#     db.commit()
#     return True

# #CRUDs for Firmware
# def download_firmware(db: Session, firmware_id: int):
#     """
#     Получить информацию о прошивке для скачивания
#     """
#     fw = db.query(models.Firmwares).filter(models.Firmwares.id_Firmwares == firmware_id).first()
#     if not fw:
#         return None
#     return fw

# def get_firmwares_by_terminal(db: Session, id_Firmwares: str):
#     return db.query(models.Firmwares).filter(models.Firmwares.id_Firmwares == id_Firmwares).first()

# def create_firmwares(db: Session, firmwares: schemas.FirmwareSchema):
#     db_firmwares = models.Firmwares(
#         id_Firmwares = firmwares.id_Firmwares,
#         inner_version = firmwares.inner_version,
#         producer_version = firmwares.producer_version,
#         download_link = firmwares.download_link,
#         release_date = firmwares.release_date,
#         maj_to = firmwares.maj_to,
#         min_to = firmwares.min_to,
#         maj_for_c_model = firmwares.maj_for_c_model,
#         min_for_c_model = firmwares.min_for_c_model,
#         time_Maj = firmwares.time_Maj,
#         time_Min = firmwares.time_Min
#     )
#     db.add(db_firmwares)
#     db.commit()
#     db.refresh(db_firmwares)
#     return db_firmwares

# def delete_firmwares(db: Session, firmwares_id: int):
#     firmwares = db.query(models.Firmwares).filter(models.Firmwares.id_Firmwares == firmwares_id).first()
#     if firmwares is None:
#         return False
#     db.delete(firmwares)
#     db.commit()
#     return True



# #CRUDs for TrueComponents
# def get_true_component_by_terminal(db: Session, id: str):
#     return db.query(models.TrueComponents).filter(models.TrueComponents.id == id).first()

# def create_true_component(db: Session, true_component: schemas.TrueComponentSchema):
#     db_true_component = models.TrueComponents(
#         id = true_component.id,
#         Type_component = true_component.Type_component,
#         Model_component = true_component.Model_component,
#         Year_component = true_component.Year_component,
#     )
#     db.add(db_true_component)
#     db.commit()
#     db.refresh(db_true_component)
#     return db_true_component

# def delete_true_component(db: Session, true_component_id: int):
#     true_component = db.query(models.TrueComponents).filter(models.TrueComponents.id == true_component_id).first()
#     if true_component is None:
#         return False
#     db.delete(true_component)
#     db.commit()
#     return True

# #Большой поиск по фильтрам(надо сделать)
# def get_tractor_software(db: Session, filters: schemas.TractorFilter):
#     query = (
#         db.query(models.Tractors)
#         .join(models.TractorComponent)
#         .join(models.TelemetryComponents)
#         .join(models.Firmwares)
#         .join(models.TrueComponents, models.TelemetryComponents.true_comp == models.TrueComponents.id)
#     )

#     # 1. Фильтр по моделям трактора
#     if filters.models:
#         query = query.filter(models.Tractors.model.in_(filters.models))

#     # 2. Фильтр по дате выпуска (assembly_date)
#     if filters.release_date_from:
#         date_from = datetime.fromisoformat(filters.release_date_from)
#         query = query.filter(models.Tractors.assembly_date >= date_from)
#     if filters.release_date_to:
#         date_to = datetime.fromisoformat(filters.release_date_to)
#         query = query.filter(models.Tractors.assembly_date <= date_to)

#     # 3. Фильтр по MAJ/MIN
#     if filters.requires_maj:
#         query = query.filter(models.TelemetryComponents.is_maj == True)
#     if filters.requires_min:
#         query = query.filter(models.TelemetryComponents.is_maj == False)

#     tractors = query.all()

#     # Формируем ответ
#     result = []
#     for tractor in tractors:
#         components = []
#         for tc in tractor.comp_list:
#             fw = tc.comp_rel.firmware_rel
#             true_comp = tc.comp_rel.true_rel

#             components.append({
#                 "type_component": true_comp.Type_component,
#                 "model_component": true_comp.Model_component,
#                 "year_component": true_comp.Year_component.isoformat() if true_comp.Year_component else None,
#                 "current_version": tc.comp_rel.current_version,
#                 "is_maj": tc.comp_rel.is_maj,
#                 "firmware": {
#                     "inner_version": fw.inner_version,
#                     "producer_version": fw.producer_version,
#                     "download_link": fw.download_link,
#                     "release_date": fw.release_date.isoformat() if fw.release_date else None,
#                     "maj_to": fw.maj_to,
#                     "min_to": fw.min_to,
#                 }
#             })

#         result.append({
#             "vin": str(tractor.terminal_id),
#             "model": tractor.model,
#             "assembly_date": tractor.assembly_date.isoformat() if tractor.assembly_date else None,
#             "region": tractor.region,
#             "dvс": "Н/Д",
#             "kpp": "Н/Д",
#             "pk": "Н/Д",
#             "bk": "Н/Д",
#             "components": components
#         })

#     return result


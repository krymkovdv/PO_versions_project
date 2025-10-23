from sqlalchemy.orm import Session
from datetime import datetime
from . import models, schemas
from sqlalchemy import and_, or_, func
from sqlalchemy import cast, String

#Большой поиск по фильтрам(непроверено)
def get_tractor_software(db: Session, filters: schemas.TractorFilter):
    """
    Получить список тракторов с их ПО по фильтрам
    """

    query = db.query(models.Tractors).join(models.TractorComponent).join(models.TelemetryComponents).join(models.Firmwares)

    # Фильтр по моделям трактора
    if filters.models:
        query = query.filter(models.Tractors.model.in_(filters.models))

    # Фильтр по дате выпуска
    if filters.release_date_from:
        date_from = datetime.fromisoformat(filters.release_date_from)
        query = query.filter(models.Tractors.assembly_date >= date_from)
    if filters.release_date_to:
        date_to = datetime.fromisoformat(filters.release_date_to)
        query = query.filter(models.Tractors.assembly_date <= date_to)

    # Фильтр по типу компонента (через TrueComponents)
    if filters.component_types:
        query = query.join(models.TelemetryComponents.true_comp).filter(
            models.TrueComponents.Type_component.in_(filters.component_types)
        )

    # Фильтр по требованию MAJ/MIN
    if filters.requires_maj:
        query = query.filter(models.TelemetryComponents.is_maj == True)
    if filters.requires_min:
        # Это сложнее — нужно проверять, что текущая версия != Maj_for_c_model/Min_for_c_model
        # Но в вашей модели нет прямой связи. Можно сделать через подзапрос или логику в приложении.
        # Пока просто фильтруем по is_maj=False, если требуется MIN
        query = query.filter(models.TelemetryComponents.is_maj == False)

    # Умный поиск (по VIN, модели, дилеру и т.д.)
    if filters.search_query:
        search = f"%{filters.search_query}%"
        query = query.filter(
            or_(
                cast(models.Tractors.terminal_id, String).like(search),  # если terminal_id = VIN
                models.Tractors.model.like(search),
                models.Tractors.owner_name.like(search),
                models.Tractors.region.like(search)
            )
        )

    tractors = query.all()

    result = []
    for tractor in tractors:
        row = {
            "vin": str(tractor.terminal_id),  # временно
            "model": tractor.model,
            "assembly_date": tractor.assembly_date.isoformat(),
            "region": tractor.region,
            # "motocycles": 0,  # нет поля в модели — нужно добавить
            # "last_activity": "N/A",  # нет поля — нужно добавить
            "dvс": "Номер ПО / необходимость обновления",
            "kpp": "Номер ПО / необходимость обновления",
            "pk": "Номер ПО / необходимость обновления",
            "bk": "Номер ПО / необходимость обновления",
            "components": []
        }

        for tc in tractor.comp_list:
            comp = tc.comp_rel
            fw = comp.firmware_rel
            component_info = {
                "type_component": comp.true_rel.Type_component,
                "model_component": comp.true_rel.Model_component,
                "year_component": comp.true_rel.Year_component.isoformat(),
                "current_version": comp.current_version,
                "is_maj": comp.is_maj,
                "firmware": {
                    "inner_version": fw.inner_version,
                    "producer_version": fw.producer_version,
                    "download_link": fw.download_link,
                    "release_date": fw.release_date.isoformat() if fw.release_date else None,
                    "maj_to": fw.maj_to,
                    "min_to": fw.min_to
                }
            }
            row["components"].append(component_info)

        result.append(row)

    return result


#Cruds for Tractor
def smart_search_tractors(db: Session, query: str):
    """
    Умный поиск по VIN, модели, дилеру, региону
    """
    search = f"%{query}%"
    tractors = db.query(models.Tractors).filter(
        or_(
            cast(models.Tractors.terminal_id, String).like(search),
            models.Tractors.model.like(search),
            models.Tractors.owner_name.like(search),
            models.Tractors.region.like(search)
        )
    ).all()

    return tractors

def create_tractor(db: Session, tractor: schemas.TractorsSchema):
    db_tractor = models.Tractors(
        terminal_id=tractor.terminal_id,
        model=tractor.model,
        region=tractor.region,
        owner_name=tractor.owner_name,
        assembly_date=tractor.assembly_date or datetime.utcnow()
    )
    db.add(db_tractor)
    db.commit()
    db.refresh(db_tractor)
    return db_tractor

def get_tractor_by_terminal(db: Session, terminal_id: str):
    return db.query(models.Tractors).filter(models.Tractors.terminal_id == terminal_id).first()

def delete_tractor(db: Session, tractor_id: int):
    tractor = db.query(models.Tractors).filter(models.Tractors.terminal_id == tractor_id).first()
    if tractor is None:
        return False
    db.delete(tractor)
    db.commit()
    return True


#Cruds for TractorComponent
def get_tractor_component_by_terminal(db: Session, row_id: str):
    return db.query(models.TractorComponent).filter(models.TractorComponent.row_id == row_id).first()

def create_tractor_component(db: Session, tractor_component: schemas.TractorsComponentSchema):
    db_tractor_component = models.TractorComponent(
        row_id = tractor_component.row_id,
        time_comp = tractor_component.time_comp,
        tractor= tractor_component.tractor,
        comp_id = tractor_component.comp_id
    )
    db.add(db_tractor_component)
    db.commit()
    db.refresh(db_tractor_component)
    return db_tractor_component

def delete_tractor_component(db: Session, tractor_component_row_id: int):
    tractor_component = db.query(models.TractorComponent).filter(models.TractorComponent.row_id == tractor_component_row_id).first()
    if tractor_component is None:
        return False
    db.delete(tractor_component)
    db.commit()
    return True

#CRUDs for TelemetryComponent
def get_telemetry_component_by_terminal(db: Session, id_telemetry: str):
    return db.query(models.TelemetryComponents).filter(models.TelemetryComponents.id_telemetry == id_telemetry).first()

def create_telemetry_component(db: Session, telemetry_component: schemas.TelemetryComponentSchema):
    db_telemetry_component = models.TelemetryComponents(
        id_telemetry = telemetry_component.id_telemetry,
        current_version = telemetry_component.current_version,
        true_comp = telemetry_component.true_comp,
        is_maj = telemetry_component.is_maj
    )
    db.add(db_telemetry_component)
    db.commit()
    db.refresh(db_telemetry_component)
    return db_telemetry_component

def delete_telemetry_component(db: Session, telemetry_component_id_telemetry: int):
    telemetry_component = db.query(models.TelemetryComponents).filter(models.TelemetryComponents.id_telemetry == telemetry_component_id_telemetry).first()
    if telemetry_component is None:
        return False
    db.delete(telemetry_component)
    db.commit()
    return True

#CRUDs for Firmware
def download_firmware(db: Session, firmware_id: int):
    """
    Получить информацию о прошивке для скачивания
    """
    fw = db.query(models.Firmwares).filter(models.Firmwares.id_Firmwares == firmware_id).first()
    if not fw:
        return None
    return fw

def get_firmwares_by_terminal(db: Session, id_Firmwares: str):
    return db.query(models.Firmwares).filter(models.Firmwares.id_Firmwares == id_Firmwares).first()

def create_firmwares(db: Session, firmwares: schemas.FirmwareSchema):
    db_firmwares = models.Firmwares(
        id_Firmwares = firmwares.id_Firmwares,
        inner_version = firmwares.inner_version,
        producer_version = firmwares.producer_version,
        download_link = firmwares.download_link,
        release_date = firmwares.release_date,
        maj_to = firmwares.maj_to,
        min_to = firmwares.min_to,
        maj_for_c_model = firmwares.maj_for_c_model,
        min_for_c_model = firmwares.min_for_c_model,
        time_Maj = firmwares.time_Maj,
        time_Min = firmwares.time_Min
    )
    db.add(db_firmwares)
    db.commit()
    db.refresh(db_firmwares)
    return db_firmwares

def delete_firmwares(db: Session, firmwares_id: int):
    firmwares = db.query(models.Firmwares).filter(models.Firmwares.id_Firmwares == firmwares_id).first()
    if firmwares is None:
        return False
    db.delete(firmwares)
    db.commit()
    return True



#CRUDs for TrueComponents
def get_true_component_by_terminal(db: Session, id: str):
    return db.query(models.TrueComponents).filter(models.TrueComponents.id == id).first()

def create_true_component(db: Session, true_component: schemas.TrueComponentSchema):
    db_true_component = models.TrueComponents(
        id = true_component.id,
        Type_component = true_component.Type_component,
        Model_component = true_component.Model_component,
        Year_component = true_component.Year_component,
    )
    db.add(db_true_component)
    db.commit()
    db.refresh(db_true_component)
    return db_true_component

def delete_true_component(db: Session, true_component_id: int):
    true_component = db.query(models.TrueComponents).filter(models.TrueComponents.id == true_component_id).first()
    if true_component is None:
        return False
    db.delete(true_component)
    db.commit()
    return True


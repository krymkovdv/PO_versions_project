from sqlalchemy.orm import Session
from datetime import datetime
from . import models, schemas
from sqlalchemy import and_, or_, func
from sqlalchemy import cast, String

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


def download_firmware(db: Session, firmware_id: int):
    """
    Получить информацию о прошивке для скачивания
    """
    fw = db.query(models.Firmwares).filter(models.Firmwares.id_Firmwares == firmware_id).first()
    if not fw:
        return None
    return fw


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


def create_tractor(db: Session, tractor: schemas.TractorCreate):
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


def get_tractor(db: Session, tractor_id: int):
    return db.query(models.Tractors).filter(models.Tractors.id == tractor_id).first()

def get_tractor_by_terminal(db: Session, terminal_id: str):
    return db.query(models.Tractors).filter(models.Tractors.terminal_id == terminal_id).first()


def delete_tractor(db: Session, tractor_id: int):
    tractor = db.query(models.Tractors).filter(models.Tractors.terminal_id == tractor_id).first()
    if tractor is None:
        return False
    db.delete(tractor)
    db.commit()
    return True
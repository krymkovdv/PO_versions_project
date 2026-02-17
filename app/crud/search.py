from sqlalchemy.orm import Session
from .. import models, schemas
from sqlalchemy import select, or_, exists
from typing import List
from datetime import timedelta, datetime
import re
import logging

logger = logging.getLogger(__name__)


#CRUD'ы для страницы 3
def get_component_by_filters(
    db: Session,
    trac_model: List[str],
    type_comp: List[str],
    model_comp: List[str]
):
    query = (
        db.query(
            models.Software.id,
            models.Software.path.label("download_link"),
            models.Software.name.label("producer_version"),
            models.Software.inner_name.label("inner_version"),
            models.Software.release_date,
            models.Software.id.label("id_Firmwares"),
            models.Component.type.label("type_component"),
            models.Component.model.label("model_component"),
            models.Software2ComponentPart.is_actual.label("is_actual")
        )
        .select_from(models.Component)
        .outerjoin(models.TelemetryComponents, models.Component.id == models.TelemetryComponents.component)
        .outerjoin(models.Tractors, models.TelemetryComponents.tractor == models.Tractors.id)
        .outerjoin(models.ComponentParts, models.Component.id == models.ComponentParts.component)
        .outerjoin(models.Software, models.TelemetryComponents.current_sw_version == models.Software.id)
        .outerjoin(models.Software2ComponentPart, models.Software2ComponentPart.software_id == models.Software.id)
    )

    if trac_model:
        query = query.filter(models.Tractors.model.in_(trac_model))
    if type_comp:
        query = query.filter(models.Component.type.in_(type_comp))
    if model_comp:
        query = query.filter(models.Component.model.in_(model_comp))

    query = query.distinct()
    results = query.all()

    return [
        {
            "download_link": r.download_link,
            "type_component": r.type_component,
            "release_date": r.release_date.isoformat() if r.release_date else None,
            "inner_version": r.inner_version,
            "producer_version": r.producer_version,
            "is_maj": r.is_actual,
            "model_component": r.model_component,
            "id_Firmwares": r.id_Firmwares
        }
        for r in results
    ]

def search_components(db: Session, model_comp: str):
    query = (
        db.query(
            models.Software.id,
            models.Software.path.label("download_link"),
            models.Software.name.label("producer_version"),
            models.Software.inner_name.label("inner_version"),
            models.Software.release_date,
            models.Software.id.label("id_Firmwares"),
            models.Component.type.label("type_component"),
            models.Component.model.label("model_component"),
            models.Software2ComponentPart.is_actual.label("is_actual")
        )
        .select_from(models.Component)
        .outerjoin(models.TelemetryComponents, models.Component.id == models.TelemetryComponents.component)
        .outerjoin(models.Tractors, models.TelemetryComponents.tractor == models.Tractors.id)
        .outerjoin(models.ComponentParts, models.Component.id == models.ComponentParts.component)
        .outerjoin(models.Software, models.TelemetryComponents.current_sw_version == models.Software.id)
        .outerjoin(models.Software2ComponentPart, models.Software2ComponentPart.software_id == models.Software.id)
    )

    if model_comp:
        user_input = model_comp.strip()
        if user_input:
            try:
                regex_pattern = schemas.wildcard_to_psql_regex(user_input)
                if not schemas.is_safe_regex(regex_pattern):
                    raise ValueError("Слишком сложный или потенциально опасный поисковый запрос")
                query = query.filter(models.Component.model.op('~*')(regex_pattern))
            except re.error as e:
                raise ValueError(f"Некорректный поисковый шаблон: {str(e)}")
            except Exception as e:
                raise ValueError(f"Ошибка при поиске: {str(e)}")

    query = query.distinct()
    results = query.all()

    return [
        {
            "download_link": r.download_link,
            "type_component": r.type_component,
            "release_date": r.release_date.isoformat() if r.release_date else None,
            "inner_version": r.inner_version,
            "producer_version": r.producer_version,
            "is_maj": r.is_maj,
            "model_component": r.model_component,
            "id_Firmwares": r.id_Firmwares
        }
        for r in results
    ]

# --- CRUD для Tractor Info (страница 4) ---

def get_tractors_by_filters(db: Session, filter: schemas.TractorFilter):
    tractors_needing_major_update = select(models.Tractors.id).join(
        models.TelemetryComponents, models.Tractors.id == models.TelemetryComponents.tractor
    ).join(
        models.Component, models.TelemetryComponents.component == models.Component.id
    ).join(
        models.ComponentParts, models.Component.id == models.ComponentParts.component
    ).join(
        models.Software2ComponentPart, models.ComponentParts.id == models.Software2ComponentPart.component_part_id
    ).where(
        models.Software2ComponentPart.is_actual == True,
        models.Software2ComponentPart.date_change_actual.isnot(None),
        models.Software2ComponentPart.software_id != models.TelemetryComponents.current_sw_version
    ).distinct(models.Tractors.id).subquery()

    # Основной запрос — ТОЛЬКО Tractors
    query = db.query(
        models.Tractors.vin,
        models.Tractors.model,
        models.Tractors.consumer,
        models.Tractors.assembly_date,
        models.Tractors.region,
        models.Tractors.oh_hour,
        models.Tractors.last_activity,
    ).select_from(models.Tractors)

    # Применяем фильтр по is_major
    if filter.is_actual is not None:
        if filter.is_actual:
            query = query.filter(models.Tractors.id.in_(select(tractors_needing_major_update.c.id)))
        else:
            query = query.filter(~models.Tractors.id.in_(select(tractors_needing_major_update.c.id)))

    # Фильтры по модели, дилеру, дате, поиску — остаются как есть
    if filter.trac_model:
        query = query.filter(models.Tractors.model.in_(filter.trac_model))

    if filter.dealer:
        dealer_pattern = schemas.wildcard_to_psql_regex(filter.dealer)
        if not schemas.is_safe_regex(dealer_pattern):
            raise ValueError("Слишком сложный поисковый запрос для дилера")
        layout_regex = _similar_chars(dealer_pattern)
        query = query.filter(models.Tractors.consumer.op('~*')(layout_regex))

    if filter.query:
        q = filter.query.strip()
        if q:
            try:
                regex_pattern = schemas.wildcard_to_psql_regex(q)
                if not schemas.is_safe_regex(regex_pattern):
                    raise ValueError("Слишком сложный поисковый запрос")
                layout_regex = _similar_chars(regex_pattern)
                or_conditions = [
                    models.Tractors.vin.op('~*')(layout_regex),
                    models.Tractors.model.op('~*')(layout_regex),
                ]
                query = query.filter(or_(*or_conditions))
            except Exception as e:
                raise ValueError(f"Ошибка поиска: {str(e)}")

    if filter.date_assemle:
        try:
            if isinstance(filter.date_assemle, str):
                filter_date = datetime.strptime(filter.date_assemle, '%Y-%m-%d').date()
            else:
                filter_date = filter.date_assemle
            next_day = filter_date + timedelta(days=1)
            query = query.filter(
                models.Tractors.assembly_date >= filter_date,
                models.Tractors.assembly_date < next_day
            )
        except (ValueError, TypeError) as e:
            print(f"Ошибка преобразования даты: {e}")
    elif filter.date_start or filter.date_end:
        if filter.date_start and not filter.date_end:
            query = query.filter(models.Tractors.assembly_date >= filter.date_start)
        elif filter.date_end and not filter.date_start:
            query = query.filter(models.Tractors.assembly_date <= filter.date_end)
        elif filter.date_start and filter.date_end:
            query = query.filter(
                models.Tractors.assembly_date >= filter.date_start,
                models.Tractors.assembly_date <= filter.date_end
            )
    if filter.status:
        exists_condition = (
            select(1)
            .select_from(models.TelemetryComponents)
            .join(
                models.Software2ComponentPart,
                models.TelemetryComponents.current_sw_version == models.Software2ComponentPart.software_id
            )
            .where(
                models.TelemetryComponents.tractor == models.Tractors.id,
                models.Software2ComponentPart.status.in_(filter.status)
            )
        )
        query = query.filter(exists(exists_condition))

    query = query.distinct()
    results = query.all()
    return [
        {
            "vin": r.vin,
            "model": r.model,
            "consumer": r.consumer,
            "assembly_date": r.assembly_date.isoformat() if r.assembly_date else None,
            "region": r.region,
            "oh_hour": str(r.oh_hour) if r.oh_hour is not None else "",
            "last_activity": r.last_activity.isoformat() if r.last_activity else None,
        }
        for r in results
    ]

# def search_tractors(db: Session, request: str):
#     query = (
#         db.query(
#             models.Tractors.vin,
#             models.Tractors.model,
#             models.Tractors.consumer,
#             models.Tractors.assembly_date,
#             models.Tractors.region,
#             models.Tractors.oh_hour,
#             models.Tractors.last_activity,
#             models.Software.name,
#             models.ComponentParts.id.label("componentPart_id"),
#             models.Component.id.label("component_id"),
#             models.Component.model.label("comp_model"),
#             models.TelemetryComponents.recommend_sw_version,
#             models.TelemetryComponents.current_sw_version, 
#             models.Software.description,
#             models.Component.type
#         )
#         .select_from(models.Tractors)
#         .outerjoin(models.TelemetryComponents, models.Tractors.id == models.TelemetryComponents.tractor)
#         .outerjoin(models.Component, models.TelemetryComponents.component == models.Component.id)
#         .outerjoin(models.ComponentParts, models.Component.id == models.ComponentParts.component)
#         .outerjoin(models.Software, models.TelemetryComponents.current_sw_version == models.Software.id)
#         .outerjoin(models.Software2ComponentPart, models.Software2ComponentPart.software_id == models.Software.id)
#     )

#     if request:
#         q = request.strip()
#         if q:
#             try:
#                 regex_pattern = schemas.wildcard_to_psql_regex(q)
#                 if not schemas.is_safe_regex(regex_pattern):
#                     raise ValueError("Слишком сложный поисковый запрос")
#                 layout_regex = _similar_chars(regex_pattern)
#                 or_conditions = [
#                     models.Tractors.vin.op('~*')(layout_regex),
#                     models.Tractors.model.op('~*')(layout_regex),
#                     models.Software.name.op('~*')(layout_regex),
#                     models.Component.model.op('~*')(layout_regex),
#                 ]
#                 query = query.filter(or_(*or_conditions))
#             except Exception as e:
#                 raise ValueError(f"Ошибка поиска: {str(e)}")

#     query = query.distinct()
#     results = query.all()

#     return [
#         {
#             "vin": r.vin,
#             "model": r.model,
#             "consumer": r.consumer,
#             "assembly_date": r.assembly_date.isoformat() if r.assembly_date else None,
#             "region": r.region,
#             "oh_hour": str(r.oh_hour) if r.oh_hour is not None else "",
#             "last_activity": r.last_activity.isoformat() if r.last_activity else None,
#             "sw_name": r.name,
#             "componentParts_id": r.componentPart_id,
#             "component_id": r.component_id,
#             "comp_model": r.comp_model,
#             "current_sw_version": r.current_sw_version,
#             "description": r.description if r.description is not None else "",
#             "recommend_sw_version": str(r.recommend_sw_version) if r.recommend_sw_version is not None else "",
#             "component_type": r.type
#         }
#         for r in results
#     ]
def _similar_chars(regex_pattern: str) -> str:
    similar_chars = {
        'а': '[аa]', 'е': '[еe]', 'к': '[кk]', 'о': '[оo]', 'р': '[рp]',
        'с': '[сc]', 'у': '[уy]', 'х': '[хx]', 'м': '[мm]', 'н': '[нh]',
        'т': '[тt]', 'в': '[вb]',
        'a': '[aа]', 'e': '[eе]', 'k': '[kк]', 'o': '[oо]', 'p': '[pр]',
        'c': '[cс]', 'y': '[yу]', 'x': '[xх]', 'm': '[mм]', 'h': '[hн]',
        't': '[tт]', 'b': '[bв]'
    }

    result = []
    for char in regex_pattern:
        if char.lower() in similar_chars:
            if char.isupper():
                variants = similar_chars[char.lower()]
                result.append(f'({variants.upper()}|{variants})')
            else:
                result.append(similar_chars[char])
        else:
            result.append(char)
    return ''.join(result)

def get_tractor_by_vin(db: Session, vin: str):
    
    tractor = db.query(models.Tractors).filter(models.Tractors.vin == vin).first()
    
    if not tractor:
      return []
    query = (
        db.query(
            models.Tractors.vin,
            models.Tractors.model,
            models.Tractors.consumer,
            models.Tractors.assembly_date,
            models.Tractors.region,
            models.Tractors.oh_hour,
            models.Tractors.last_activity,
            models.Software.name,
            models.Software.description,
            models.Component.id.label("component_id"),
            models.Component.model.label("comp_model"),
            models.TelemetryComponents.current_sw_version,
            models.TelemetryComponents.recommend_sw_version, 
            models.Component.type
        )
        .select_from(models.Tractors)
        .join(models.TelemetryComponents, models.Tractors.id == models.TelemetryComponents.tractor)
        .join(models.Component, models.TelemetryComponents.component == models.Component.id)
        .outerjoin(models.Software, models.TelemetryComponents.current_sw_version == models.Software.id) 
        .filter(models.Tractors.vin == vin)
    )

    results = query.all()

    if results:
        return [
            {
                "vin": r.vin,
                "model": r.model,
                "consumer": r.consumer,
                "assembly_date": r.assembly_date.isoformat() if r.assembly_date else None,
                "region": r.region,
                "oh_hour": str(r.oh_hour) if r.oh_hour is not None else "",
                "last_activity": r.last_activity.isoformat() if r.last_activity else None,
                "sw_name": r.name,
                "description": r.description,
                "component_id": r.component_id,
                "comp_model": r.comp_model,
                "current_sw_version": r.current_sw_version,
                "recommend_sw_version": str(r.recommend_sw_version) if r.recommend_sw_version is not None else "",
                "component_type": r.type
            }
            for r in results
        ]
    else:
        # Если нет компонентов, возвращаем только информацию о тракторе
        return [{
            "vin": tractor.vin,
            "model": tractor.model,
            "consumer": tractor.consumer,
            "assembly_date": tractor.assembly_date.isoformat() if tractor.assembly_date else None,
            "region": tractor.region,
            "oh_hour": str(tractor.oh_hour) if tractor.oh_hour is not None else "",
            "last_activity": tractor.last_activity.isoformat() if tractor.last_activity else None,
            "sw_name": None,
            "description": None,
            "component_id": None,
            "comp_model": None,
            "current_sw_version": None,
            "recommend_sw_version": None,
            "component_type": None
        }]

def get_all_components_with_part(db: Session):
    stmt = (
        select(
            models.Component.id,
            models.Component.model,
            models.ComponentParts.part_type
        )
        .join(models.ComponentParts, models.Component.id == models.ComponentParts.component)
        .order_by(models.Component.model, models.ComponentParts.part_type)
    )

    result = db.execute(stmt).all()

    return [
        {
            "model(part)": f"{row.model} ({row.part_type})",
            "model": row.model,
            "part_type": row.part_type
        }
        for row in result
    ]
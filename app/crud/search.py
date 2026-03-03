from sqlalchemy.orm import Session
from .. import models, schemas
from sqlalchemy import select, or_, exists, distinct
from typing import List, Optional
from datetime import timedelta, datetime
import re
import logging

logger = logging.getLogger(__name__)

# ============================================
# Страница 3: Компоненты и ПО
# ============================================
def get_component_by_filters(
    db: Session,
    trac_model: List[str] = None,
    type_comp: List[str] = None,
    comp_name: List[str] = None,
    producers: List[str] = None,
    status: List[str] = None
):
    """Получить ПО по фильтрам (обновлено для новой схемы)"""
    
    query = (
        db.query(
            models.Software.id.label("id_Firmwares"),
            models.Software.path.label("download_link"),
            models.Software.release_date,
            models.Software.description,
            models.Software.is_actual,
            models.Software.status,
            models.Component.type,
            models.Component.name,
            models.Component.producer
        )
        .select_from(models.Software)
        .join(
            models.Software_Component_Link,
            models.Software.id == models.Software_Component_Link.software_id
        )
        .join(
            models.Component,
            models.Software_Component_Link.component_id == models.Component.id
        )
    )

    # Фильтры
    if trac_model:
        query = query.filter(models.Software.tractor_model.in_(trac_model))
    if type_comp:
        query = query.filter(models.Component.type.in_(type_comp))
    if comp_name:
        query = query.filter(models.Component.name.in_(comp_name))
    if producers:
        query = query.filter(models.Component.producer.in_(producers))
    if status:
        query = query.filter(models.Software.status.in_(status))

    query = query.distinct()
    results = query.all()

    return [
        {
            "download_link": r.download_link,
            "type": r.type,
            "release_date": r.release_date.isoformat() if r.release_date else None,
            "producer": r.producer,
            "is_actual": r.is_actual,
            "name_component": r.name,
            "id_Firmwares": r.id_Firmwares,
            "status": r.status,
        }
        for r in results
    ]


def search_components(db: Session, model_comp: str):
    """Поиск компонентов по regex-шаблону"""
    
    query = (
        db.query(
            models.Software.id.label("id_Firmwares"),
            models.Software.path.label("download_link"),
            models.Software.name.label("producer_version"),
            models.Software.inner_name.label("inner_version"),
            models.Software.release_date,
            models.Software.is_actual,
            models.Component.type.label("type_component"),
            models.Component.name.label("model_component")
        )
        .select_from(models.Software)
        .join(
            models.Software_Component_Link,
            models.Software.id == models.Software_Component_Link.software_id
        )
        .join(
            models.Component,
            models.Software_Component_Link.component_id == models.Component.id
        )
    )

    if model_comp:
        user_input = model_comp.strip()
        if user_input:
            try:
                regex_pattern = schemas.wildcard_to_psql_regex(user_input)
                if not schemas.is_safe_regex(regex_pattern):
                    raise ValueError("Слишком сложный или потенциально опасный поисковый запрос")
                query = query.filter(models.Component.name.op('~*')(regex_pattern))
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
            "is_maj": r.is_actual,
            "model_component": r.model_component,
            "id_Firmwares": r.id_Firmwares
        }
        for r in results
    ]


# ============================================
# Страница 4: Тракторы
# ============================================
def get_tractors_by_filters(db: Session, filter: schemas.TractorFilter):
    """Получить тракторы по фильтрам (обновлено для новой схемы)"""
    
    # Подзапрос для тракторов с актуальными обновлениями
    tractors_needing_update = (
        select(models.Tractor.id)
        .join(
            models.Tractor_Software_And_Component_Link,
            models.Tractor.id == models.Tractor_Software_And_Component_Link.tractor_id
        )
        .join(
            models.Software_Component_Link,
            models.Tractor_Software_And_Component_Link.soft_comp_link_id == models.Software_Component_Link.id
        )
        .join(
            models.Software,
            models.Software_Component_Link.software_id == models.Software.id
        )
        .where(
            models.Software.is_actual == True,
            models.Software.is_archive == False
        )
        .distinct()
        .subquery()
    )

    # Основной запрос
    query = db.query(
        models.Tractor.id,
        models.Tractor.vin,
        models.Tractor.model,
        models.Tractor.consumer.label("dealer"),
        models.Tractor.assembly_date,
        models.Tractor.region,
        models.Tractor.oh_hour,
        models.Tractor.last_activity,
        models.Tractor.dealer
    ).select_from(models.Tractor)

    # Фильтр по is_actual
    if filter.is_actual is not None:
        if filter.is_actual:
            query = query.filter(models.Tractor.id.in_(select(tractors_needing_update.c.id)))
        else:
            query = query.filter(~models.Tractor.id.in_(select(tractors_needing_update.c.id)))

    # Фильтры
    if filter.trac_model:
        query = query.filter(models.Tractor.model.in_(filter.trac_model))

    if filter.dealer:
        dealer_pattern = schemas.wildcard_to_psql_regex(filter.dealer)
        if not schemas.is_safe_regex(dealer_pattern):
            raise ValueError("Слишком сложный поисковый запрос для дилера")
        layout_regex = _similar_chars(dealer_pattern)
        query = query.filter(models.Tractor.consumer.op('~*')(layout_regex))

    if filter.query:
        q = filter.query.strip()
        if q:
            try:
                regex_pattern = schemas.wildcard_to_psql_regex(q)
                if not schemas.is_safe_regex(regex_pattern):
                    raise ValueError("Слишком сложный поисковый запрос")
                layout_regex = _similar_chars(regex_pattern)
                or_conditions = [
                    models.Tractor.vin.op('~*')(layout_regex),
                    models.Tractor.model.op('~*')(layout_regex),
                ]
                query = query.filter(or_(*or_conditions))
            except Exception as e:
                raise ValueError(f"Ошибка поиска: {str(e)}")

    # Даты
    if filter.date_assemle:
        try:
            if isinstance(filter.date_assemle, str):
                filter_date = datetime.strptime(filter.date_assemle, '%Y-%m-%d').date()
            else:
                filter_date = filter.date_assemle
            next_day = filter_date + timedelta(days=1)
            query = query.filter(
                models.Tractor.assembly_date >= filter_date,
                models.Tractor.assembly_date < next_day
            )
        except (ValueError, TypeError) as e:
            logger.error(f"Ошибка преобразования даты: {e}")
    elif filter.date_start or filter.date_end:
        if filter.date_start and not filter.date_end:
            query = query.filter(models.Tractor.assembly_date >= filter.date_start)
        elif filter.date_end and not filter.date_start:
            query = query.filter(models.Tractor.assembly_date <= filter.date_end)
        elif filter.date_start and filter.date_end:
            query = query.filter(
                models.Tractor.assembly_date >= filter.date_start,
                models.Tractor.assembly_date <= filter.date_end
            )

    # Статус
    if filter.status:
        exists_condition = (
            select(1)
            .select_from(models.Tractor_Software_And_Component_Link)
            .join(
                models.Software_Component_Link,
                models.Tractor_Software_And_Component_Link.soft_comp_link_id == models.Software_Component_Link.id
            )
            .join(
                models.Software,
                models.Software_Component_Link.software_id == models.Software.id
            )
            .where(
                models.Tractor_Software_And_Component_Link.tractor_id == models.Tractor.id,
                models.Software.status.in_(filter.status)
            )
        )
        query = query.filter(exists(exists_condition))

    query = query.distinct()
    results = query.all()
    
    return [
        {
            "vin": r.vin,
            "model": r.model,
            "consumer": r.dealer,
            "assembly_date": r.assembly_date.isoformat() if r.assembly_date else None,
            "region": r.region,
            "oh_hour": str(r.oh_hour) if r.oh_hour is not None else "",
            "last_activity": r.last_activity.isoformat() if r.last_activity else None,
        }
        for r in results
    ]


def get_tractor_by_vin(db: Session, vin: str):
    """Получить информацию о тракторе по VIN (обновлено для новой схемы)"""
    
    tractor = db.query(models.Tractor).filter(models.Tractor.vin == vin).first()
    
    if not tractor:
        return []
    
    query = (
        db.query(
            models.Tractor.vin,
            models.Tractor.model,
            models.Tractor.consumer,
            models.Tractor.assembly_date,
            models.Tractor.region,
            models.Tractor.oh_hour,
            models.Tractor.last_activity,
            models.Software.name.label("sw_name"),
            models.Software.description,
            models.Component.id.label("component_id"),
            models.Component.name.label("comp_model"),
            models.Software.id.label("current_sw_version"),
            models.Software.id.label("recommend_sw_version"),
            models.Component.type
        )
        .select_from(models.Tractor)
        .join(
            models.Tractor_Software_And_Component_Link,
            models.Tractor.id == models.Tractor_Software_And_Component_Link.tractor_id
        )
        .join(
            models.Software_Component_Link,
            models.Tractor_Software_And_Component_Link.soft_comp_link_id == models.Software_Component_Link.id
        )
        .join(
            models.Component,
            models.Software_Component_Link.component_id == models.Component.id
        )
        .join(
            models.Software,
            models.Software_Component_Link.software_id == models.Software.id
        )
        .filter(models.Tractor.vin == vin)
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
                "sw_name": r.sw_name,
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

def get_component_models(
    db: Session,
    trac_model: List[str] = None,
    type_comp: List[str] = None
):
    """Получить модели компонентов по фильтрам"""
    
    query = db.query(
        models.Component.name
    ).select_from(models.Component).distinct()

    if type_comp:
        query = query.filter(models.Component.type.in_(type_comp))

    if trac_model:
        query = (
            query
            .join(
                models.Software_Component_Link,
                models.Component.id == models.Software_Component_Link.component_id
            )
            .join(
                models.Tractor_Software_And_Component_Link,
                models.Software_Component_Link.id == models.Tractor_Software_And_Component_Link.soft_comp_link_id
            )
            .join(
                models.Tractor,
                models.Tractor_Software_And_Component_Link.tractor_id == models.Tractor.id
            )
            .filter(models.Tractor.model.in_(trac_model))
        )

    results = query.all()
    return [r.name for r in results if r.name is not None]


# ============================================
# Вспомогательные функции
# ============================================
def _similar_chars(regex_pattern: str) -> str:
    """Замена кириллических символов на латинские аналоги для поиска"""
    
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
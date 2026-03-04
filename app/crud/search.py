from sqlalchemy.orm import Session
from .. import models, schemas
from sqlalchemy import select, or_, exists, distinct
from typing import List, Optional
from datetime import timedelta, datetime
import re
import logging
from . import software

logger = logging.getLogger(__name__)

# ============================================
# Страница 3: Компоненты и ПО
# ============================================
def get_component_by_filters(
    db: Session,
    trac_model: list = None,
    type_comp: list = None,
    name_comp: list = None,
    producers: list = None,
    status: list = None
):
    """
    Получение ПО по фильтрам с поддержкой множественных моделей тракторов
    """
    from sqlalchemy import or_
    
    query = (
        db.query(
            models.Software.id.label("id_Firmwares"),
            models.Software.path.label("download_link"),
            models.Software.path_instruction.label("download_link_instruction"),
            models.Software.release_date,
            models.Software.is_actual,
            models.Software.is_archive,
            models.Software.is_critical,
            models.Software.status,
            models.Software.tractor_model,
            models.Component.type,
            models.Component.name,
            models.Component.id.label("id_Component")
        )
        .select_from(models.Software)
        .join(
            models.Software_Component_Link,
            models.Software.id == models.Software_Component_Link.software_id
        )
        .join(
            models.Component,
            models.Software_Component_Link.component_id == models.Component.id
        ).filter(
            models.Software.is_archive == False
        )
    )    
    if type_comp:
        query = query.filter(models.Component.type.in_(type_comp))
    
    if name_comp:
        query = query.filter(models.Component.name.in_(name_comp))
    
    if producers:
        query = query.filter(models.Component.producer.in_(producers))
    
    if status:
        query = query.filter(models.Software.status.in_(status))
    
    query = query.distinct()
    results = query.all()

    if trac_model:
        filtered_results = []
        for r in results:
            models_list = software._deserialize_tractor_models(r.tractor_model)
            # Проверяем пересечение: хотя бы одна модель из запроса есть в ПО
            if any(model in models_list for model in trac_model):
                filtered_results.append(r)
        results = filtered_results

    return [
        {
            "download_link": r.download_link,
            "download_link_instruction": getattr(r, 'download_link_instruction', None),
            "type_component": r.type,
            "release_date": r.release_date.isoformat() if r.release_date else None,
            "is_archive": r.is_archive,
            "is_actual": r.is_actual,
            "is_critical": r.is_critical,
            "name_component": r.name,
            "id_Firmwares": r.id_Firmwares,
            "id_Component":r.id_Component,
            "status": r.status,
            "tractor_model": software._deserialize_tractor_models(r.tractor_model)
        }
        for r in results
    ]

def get_archive_component_by_filters(
    db: Session,
    trac_model: list = None,
    type_comp: list = None,
    name_comp: list = None,
    producers: list = None,
    status: list = None
):
    """
    Получение ПО по фильтрам с поддержкой множественных моделей тракторов
    """
    from sqlalchemy import or_
    
    query = (
        db.query(
            models.Software.id.label("id_Firmwares"),
            models.Software.path.label("download_link"),
            models.Software.path_instruction.label("download_link_instruction"),
            models.Software.release_date,
            models.Software.is_actual,
            models.Software.is_archive,
            models.Software.is_critical,
            models.Software.status,
            models.Software.tractor_model,
            models.Component.type,
            models.Component.name,
            models.Component.id.label("id_Component")
        )
        .select_from(models.Software)
        .join(
            models.Software_Component_Link,
            models.Software.id == models.Software_Component_Link.software_id
        )
        .join(
            models.Component,
            models.Software_Component_Link.component_id == models.Component.id
        ).filter(
            models.Software.is_archive == True
        )
    )    
    if type_comp:
        query = query.filter(models.Component.type.in_(type_comp))
    
    if name_comp:
        query = query.filter(models.Component.name.in_(name_comp))
    
    if producers:
        query = query.filter(models.Component.producer.in_(producers))
    
    if status:
        query = query.filter(models.Software.status.in_(status))
    
    query = query.distinct()
    results = query.all()

    if trac_model:
        filtered_results = []
        for r in results:
            models_list = software._deserialize_tractor_models(r.tractor_model)
            # Проверяем пересечение: хотя бы одна модель из запроса есть в ПО
            if any(model in models_list for model in trac_model):
                filtered_results.append(r)
        results = filtered_results

    return [
        {
            "download_link": r.download_link,
            "download_link_instruction": getattr(r, 'download_link_instruction', None),
            "type_component": r.type,
            "release_date": r.release_date.isoformat() if r.release_date else None,
            "is_archive": r.is_archive,
            "is_actual": r.is_actual,
            "is_critical": r.is_critical,
            "name_component": r.name,
            "id_Firmwares": r.id_Firmwares,
            "id_Component":r.id_Component,
            "status": r.status,
            "tractor_model": software._deserialize_tractor_models(r.tractor_model)
        }
        for r in results
    ]


def search_components(db: Session, model_comp: str):
    """Поиск компонентов по regex-шаблону"""
    
    query = (
        db.query(
            models.Software.id.label("id_Firmwares"),
            models.Software.path.label("download_link"),
            models.Software.path_instruction.label("download_link_instruction"),
            models.Software.release_date,
            models.Software.is_actual,
            models.Software.is_archive,
            models.Software.is_critical,
            models.Software.status,
            models.Software.tractor_model,
            models.Component.type,
            models.Component.name,
            models.Component.id.label("id_Component")
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
            "download_link_instruction": getattr(r, 'download_link_instruction', None),
            "type_component": r.type,
            "release_date": r.release_date.isoformat() if r.release_date else None,
            "is_archive": r.is_archive,
            "is_actual": r.is_actual,
            "is_critical": r.is_critical,
            "name_component": r.name,
            "id_Firmwares": r.id_Firmwares,
            "id_Component":r.id_Component,
            "status": r.status,
            "tractor_model": software._deserialize_tractor_models(r.tractor_model)
        }
        for r in results
    ]

def get_software_component_by_ids(
    db: Session,
    id_firmwares: int,
    id_component: int
):
    """
    Получение полной информации о ПО и компоненте по их ID.
    
    Args:
        db: Сессия базы данных
        id_firmwares: ID программного обеспечения (Software.id)
        id_component: ID компонента (Component.id)
    
    Returns:
        Список словарей с информацией о ПО, компоненте и их связи
    """
    
    # ← 1. Базовый запрос с джойнами через таблицу связей
    query = (
        db.query(
            # ПО
            models.Software.id.label("id_firmwares"),
            models.Software.path.label("software_path"),
            models.Software.release_date.label("software_release_date"),
            models.Software.description.label("software_description"),
            models.Software.producer.label("software_producer"),
            models.Software.is_actual.label("software_is_actual"),
            models.Software.is_archive.label("software_is_archive"),
            models.Software.is_critical.label("software_is_critical"),
            models.Software.status.label("software_status"),
            models.Software.tractor_model.label("software_tractor_model"),
            models.Software.previous_sw_version.label("software_previous_sw_version"),
            models.Software.path_instruction.label("software_path_instruction"),
            
            # Компонент
            models.Component.id.label("id_component"),
            models.Component.type.label("component_type"),
            models.Component.name.label("component_name"),
            models.Component.producer.label("component_producer"),
            
            # Связь Software_Component_Link
            models.Software_Component_Link.id.label("link_id"),
            
            # Связь Tractor_Software_And_Component_Link (берём первую запись)
            models.Tractor_Software_And_Component_Link.is_recom.label("is_recom")
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
        .outerjoin(
            models.Tractor_Software_And_Component_Link,
            models.Software_Component_Link.id == models.Tractor_Software_And_Component_Link.soft_comp_link_id
        )
        .filter(
            models.Software.id == id_firmwares,
            models.Component.id == id_component,
            models.Software.is_archive == False
        )
    )
    
    results = query.all()
    
    if not results:
        return []
    
    # ← 2. Формируем ответ
    return [
        {
            # ПО
            "id_firmwares": r.id_firmwares,
            "software_path": r.software_path,
            "software_release_date": r.software_release_date.isoformat() if r.software_release_date else None,
            "software_description": r.software_description,
            "software_producer": r.software_producer,
            "software_is_actual": r.software_is_actual,
            "software_is_archive": r.software_is_archive,
            "software_is_critical": r.software_is_critical,
            "software_status": r.software_status,
            "software_tractor_models": software._deserialize_tractor_models(r.software_tractor_model) if r.software_tractor_model else [],
            "software_previous_sw_version": r.software_previous_sw_version,
            "software_path_instruction": r.software_path_instruction,
            
            # Компонент
            "id_component": r.id_component,
            "component_type": r.component_type,
            "component_name": r.component_name,
            "component_producer": r.component_producer,
            
            # Связь
            "link_id": r.link_id,
            "is_recom": r.is_recom if r.is_recom is not None else True,
        }
        for r in results
    ]

# # ============================================
# # Страница 4: Тракторы
# # ============================================
# def get_tractors_by_filters(db: Session, filter: schemas.TractorFilter):
#     """Получить тракторы по фильтрам (обновлено для новой схемы)"""
    
#     # Подзапрос для тракторов с актуальными обновлениями
#     tractors_needing_update = (
#         select(models.Tractor.id)
#         .join(
#             models.Tractor_Software_And_Component_Link,
#             models.Tractor.id == models.Tractor_Software_And_Component_Link.tractor_id
#         )
#         .join(
#             models.Software_Component_Link,
#             models.Tractor_Software_And_Component_Link.soft_comp_link_id == models.Software_Component_Link.id
#         )
#         .join(
#             models.Software,
#             models.Software_Component_Link.software_id == models.Software.id
#         )
#         .where(
#             models.Software.is_actual == True,
#             models.Software.is_archive == False
#         )
#         .distinct()
#         .subquery()
#     )

#     # Основной запрос
#     query = db.query(
#         models.Tractor.id,
#         models.Tractor.vin,
#         models.Tractor.model,
#         models.Tractor.consumer.label("dealer"),
#         models.Tractor.assembly_date,
#         models.Tractor.region,
#         models.Tractor.oh_hour,
#         models.Tractor.last_activity,
#         models.Tractor.dealer
#     ).select_from(models.Tractor)

#     # Фильтр по is_actual
#     if filter.is_actual is not None:
#         if filter.is_actual:
#             query = query.filter(models.Tractor.id.in_(select(tractors_needing_update.c.id)))
#         else:
#             query = query.filter(~models.Tractor.id.in_(select(tractors_needing_update.c.id)))

#     # Фильтры
#     if filter.trac_model:
#         query = query.filter(models.Tractor.model.in_(filter.trac_model))

#     if filter.dealer:
#         dealer_pattern = schemas.wildcard_to_psql_regex(filter.dealer)
#         if not schemas.is_safe_regex(dealer_pattern):
#             raise ValueError("Слишком сложный поисковый запрос для дилера")
#         layout_regex = _similar_chars(dealer_pattern)
#         query = query.filter(models.Tractor.consumer.op('~*')(layout_regex))

#     if filter.query:
#         q = filter.query.strip()
#         if q:
#             try:
#                 regex_pattern = schemas.wildcard_to_psql_regex(q)
#                 if not schemas.is_safe_regex(regex_pattern):
#                     raise ValueError("Слишком сложный поисковый запрос")
#                 layout_regex = _similar_chars(regex_pattern)
#                 or_conditions = [
#                     models.Tractor.vin.op('~*')(layout_regex),
#                     models.Tractor.model.op('~*')(layout_regex),
#                 ]
#                 query = query.filter(or_(*or_conditions))
#             except Exception as e:
#                 raise ValueError(f"Ошибка поиска: {str(e)}")

#     # Даты
#     if filter.date_assemle:
#         try:
#             if isinstance(filter.date_assemle, str):
#                 filter_date = datetime.strptime(filter.date_assemle, '%Y-%m-%d').date()
#             else:
#                 filter_date = filter.date_assemle
#             next_day = filter_date + timedelta(days=1)
#             query = query.filter(
#                 models.Tractor.assembly_date >= filter_date,
#                 models.Tractor.assembly_date < next_day
#             )
#         except (ValueError, TypeError) as e:
#             logger.error(f"Ошибка преобразования даты: {e}")
#     elif filter.date_start or filter.date_end:
#         if filter.date_start and not filter.date_end:
#             query = query.filter(models.Tractor.assembly_date >= filter.date_start)
#         elif filter.date_end and not filter.date_start:
#             query = query.filter(models.Tractor.assembly_date <= filter.date_end)
#         elif filter.date_start and filter.date_end:
#             query = query.filter(
#                 models.Tractor.assembly_date >= filter.date_start,
#                 models.Tractor.assembly_date <= filter.date_end
#             )

#     # Статус
#     if filter.status:
#         exists_condition = (
#             select(1)
#             .select_from(models.Tractor_Software_And_Component_Link)
#             .join(
#                 models.Software_Component_Link,
#                 models.Tractor_Software_And_Component_Link.soft_comp_link_id == models.Software_Component_Link.id
#             )
#             .join(
#                 models.Software,
#                 models.Software_Component_Link.software_id == models.Software.id
#             )
#             .where(
#                 models.Tractor_Software_And_Component_Link.tractor_id == models.Tractor.id,
#                 models.Software.status.in_(filter.status)
#             )
#         )
#         query = query.filter(exists(exists_condition))

#     query = query.distinct()
#     results = query.all()
    
#     return [
#         {
#             "vin": r.vin,
#             "model": r.model,
#             "consumer": r.dealer,
#             "assembly_date": r.assembly_date.isoformat() if r.assembly_date else None,
#             "region": r.region,
#             "oh_hour": str(r.oh_hour) if r.oh_hour is not None else "",
#             "last_activity": r.last_activity.isoformat() if r.last_activity else None,
#         }
#         for r in results
#     ]


# def get_tractor_by_vin(db: Session, vin: str):
#     """Получить информацию о тракторе по VIN (обновлено для новой схемы)"""
    
#     tractor = db.query(models.Tractor).filter(models.Tractor.vin == vin).first()
    
#     if not tractor:
#         return []
    
#     query = (
#         db.query(
#             models.Tractor.vin,
#             models.Tractor.model,
#             models.Tractor.consumer,
#             models.Tractor.assembly_date,
#             models.Tractor.region,
#             models.Tractor.oh_hour,
#             models.Tractor.last_activity,
#             models.Software.name.label("sw_name"),
#             models.Software.description,
#             models.Component.id.label("component_id"),
#             models.Component.name.label("comp_model"),
#             models.Software.id.label("current_sw_version"),
#             models.Software.id.label("recommend_sw_version"),
#             models.Component.type
#         )
#         .select_from(models.Tractor)
#         .join(
#             models.Tractor_Software_And_Component_Link,
#             models.Tractor.id == models.Tractor_Software_And_Component_Link.tractor_id
#         )
#         .join(
#             models.Software_Component_Link,
#             models.Tractor_Software_And_Component_Link.soft_comp_link_id == models.Software_Component_Link.id
#         )
#         .join(
#             models.Component,
#             models.Software_Component_Link.component_id == models.Component.id
#         )
#         .join(
#             models.Software,
#             models.Software_Component_Link.software_id == models.Software.id
#         )
#         .filter(models.Tractor.vin == vin)
#     )

#     results = query.all()

#     if results:
#         return [
#             {
#                 "vin": r.vin,
#                 "model": r.model,
#                 "consumer": r.consumer,
#                 "assembly_date": r.assembly_date.isoformat() if r.assembly_date else None,
#                 "region": r.region,
#                 "oh_hour": str(r.oh_hour) if r.oh_hour is not None else "",
#                 "last_activity": r.last_activity.isoformat() if r.last_activity else None,
#                 "sw_name": r.sw_name,
#                 "description": r.description,
#                 "component_id": r.component_id,
#                 "comp_model": r.comp_model,
#                 "current_sw_version": r.current_sw_version,
#                 "recommend_sw_version": str(r.recommend_sw_version) if r.recommend_sw_version is not None else "",
#                 "component_type": r.type
#             }
#             for r in results
#         ]
#     else:
#         return [{
#             "vin": tractor.vin,
#             "model": tractor.model,
#             "consumer": tractor.consumer,
#             "assembly_date": tractor.assembly_date.isoformat() if tractor.assembly_date else None,
#             "region": tractor.region,
#             "oh_hour": str(tractor.oh_hour) if tractor.oh_hour is not None else "",
#             "last_activity": tractor.last_activity.isoformat() if tractor.last_activity else None,
#             "sw_name": None,
#             "description": None,
#             "component_id": None,
#             "comp_model": None,
#             "current_sw_version": None,
#             "recommend_sw_version": None,
#             "component_type": None
#         }]

# def get_component_models(
#     db: Session,
#     trac_model: List[str] = None,
#     type_comp: List[str] = None
# ):
#     """Получить модели компонентов по фильтрам"""
    
#     query = db.query(
#         models.Component.name
#     ).select_from(models.Component).distinct()

#     if type_comp:
#         query = query.filter(models.Component.type.in_(type_comp))

#     if trac_model:
#         query = (
#             query
#             .join(
#                 models.Software_Component_Link,
#                 models.Component.id == models.Software_Component_Link.component_id
#             )
#             .join(
#                 models.Tractor_Software_And_Component_Link,
#                 models.Software_Component_Link.id == models.Tractor_Software_And_Component_Link.soft_comp_link_id
#             )
#             .join(
#                 models.Tractor,
#                 models.Tractor_Software_And_Component_Link.tractor_id == models.Tractor.id
#             )
#             .filter(models.Tractor.model.in_(trac_model))
#         )

#     results = query.all()
#     return [r.name for r in results if r.name is not None]


# ============================================
# Вспомогательные функции
# ============================================
def get_archive_software_component_by_ids(
    db: Session,
    id_firmwares: int,
    id_component: int
):
    """
    Получение полной информации о ПО и компоненте по их ID.
    
    Args:
        db: Сессия базы данных
        id_firmwares: ID программного обеспечения (Software.id)
        id_component: ID компонента (Component.id)
    
    Returns:
        Список словарей с информацией о ПО, компоненте и их связи
    """
    
    # ← 1. Базовый запрос с джойнами через таблицу связей
    query = (
        db.query(
            # ПО
            models.Software.id.label("id_firmwares"),
            models.Software.path.label("software_path"),
            models.Software.release_date.label("software_release_date"),
            models.Software.description.label("software_description"),
            models.Software.producer.label("software_producer"),
            models.Software.is_actual.label("software_is_actual"),
            models.Software.is_archive.label("software_is_archive"),
            models.Software.is_critical.label("software_is_critical"),
            models.Software.status.label("software_status"),
            models.Software.tractor_model.label("software_tractor_model"),
            models.Software.previous_sw_version.label("software_previous_sw_version"),
            models.Software.path_instruction.label("software_path_instruction"),
            
            # Компонент
            models.Component.id.label("id_component"),
            models.Component.type.label("component_type"),
            models.Component.name.label("component_name"),
            models.Component.producer.label("component_producer"),
            
            # Связь Software_Component_Link
            models.Software_Component_Link.id.label("link_id"),
            
            # Связь Tractor_Software_And_Component_Link (берём первую запись)
            models.Tractor_Software_And_Component_Link.is_recom.label("is_recom")
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
        .outerjoin(
            models.Tractor_Software_And_Component_Link,
            models.Software_Component_Link.id == models.Tractor_Software_And_Component_Link.soft_comp_link_id
        )
        .filter(
            models.Software.id == id_firmwares,
            models.Component.id == id_component,
            models.Software.is_archive == True
        )
    )
    
    results = query.all()
    
    if not results:
        return []
    
    # ← 2. Формируем ответ
    return [
        {
            # ПО
            "id_firmwares": r.id_firmwares,
            "software_path": r.software_path,
            "software_release_date": r.software_release_date.isoformat() if r.software_release_date else None,
            "software_description": r.software_description,
            "software_producer": r.software_producer,
            "software_is_actual": r.software_is_actual,
            "software_is_archive": r.software_is_archive,
            "software_is_critical": r.software_is_critical,
            "software_status": r.software_status,
            "software_tractor_models": software._deserialize_tractor_models(r.software_tractor_model) if r.software_tractor_model else [],
            "software_previous_sw_version": r.software_previous_sw_version,
            "software_path_instruction": r.software_path_instruction,
            
            # Компонент
            "id_component": r.id_component,
            "component_type": r.component_type,
            "component_name": r.component_name,
            "component_producer": r.component_producer,
            
            # Связь
            "link_id": r.link_id,
            "is_recom": r.is_recom if r.is_recom is not None else True,
        }
        for r in results
    ]


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



'хз куда эту функцию надо запихать максим пусть решит'


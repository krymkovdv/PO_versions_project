from sqlalchemy.orm import Session
from .. import models, schemas
from sqlalchemy import select
from typing import List
import logging
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from .software import _deserialize_tractor_models

logger = logging.getLogger(__name__)

def get_components(db: Session):
    """
    Получение всех компонентов из базы данных
    
    Args:
        db: Сессия базы данных
        
    Returns:
        Список всех компонентов
    """
    stmt = select(models.Component)
    result = db.execute(stmt).scalars().all()
    return result

def get_component_by_id(db: Session, id: int):
    """
    Получение компонента по его ID
    
    Args:
        db: Сессия базы данных
        id: ID компонента
        
    Returns:
        Компонент с указанным ID или None, если не найден
    """
    return db.query(models.Component).filter(models.Component.id == id).first()

def create_component(db: Session, component: schemas.ComponentSchema):
    """
    Создание нового компонента в базе данных
    
    Args:
        db: Сессия базы данных
        component: Данные компонента для создания
        
    Returns:
        Созданный компонент
    """
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
    """
    Удаление компонента из базы данных
    
    Args:
        db: Сессия базы данных
        id: ID компонента для удаления
        
    Returns:
        True, если компонент был удален, False, если не найден
    """
    component = db.query(models.Component).filter(models.Component.id == id).first()
    if component is None:
        return False
    db.delete(component)
    db.commit()
    return True

def update_component(db: Session, component_id: int, component_update: schemas.ComponentUpdate):
    """
    Обновление информации о компоненте
    
    Args:
        db: Сессия базы данных
        component_id: ID компонента для обновления
        component_update: Данные для обновления
        
    Returns:
        Обновленный компонент
    """
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

# app/crud/components.py

def get_agg_by_trac_and_comp(
    db: Session, 
    trac_model: List[str] = None, 
    type_comp: List[str] = None, 
    producers: List[str] = None, 
    status: List[str] = None
):
    """
    Получает уникальные модели компонентов с учётом фильтров.
    Возвращает список словарей: [{'id': 1, 'name': 'Engine-X'}, ...]
    
    Args:
        db: Сессия базы данных
        trac_model: Фильтр по моделям тракторов
        type_comp: Фильтр по типам компонентов
        producers: Фильтр по производителям
        status: Фильтр по статусу ПО
        
    Returns:
        Список словарей с ID и именами компонентов
    """
    query = db.query(
        models.Component.id,
        models.Component.name
    ).distinct()
    
    joined_software_link = False
    joined_software = False
    
    if trac_model:
        # Получаем все Software, у которых есть поле tractor_model
        software_records = db.query(models.Software).filter(
            models.Software.tractor_model.isnot(None)
        ).all()
        
        valid_software_ids = set()
        for sw in software_records:
            # Используем импортированную функцию
            models_list = _deserialize_tractor_models(sw.tractor_model)
            if any(m in models_list for m in trac_model):
                valid_software_ids.add(sw.id)
        
        # Применяем фильтр к Software_Component_Link
        if not joined_software_link:
            query = query.join(
                models.Software_Component_Link,
                models.Component.id == models.Software_Component_Link.component_id
            )
            joined_software_link = True
        query = query.filter(
            models.Software_Component_Link.software_id.in_(valid_software_ids)
        )
    
    if type_comp:
        query = query.filter(models.Component.type.in_(type_comp))
    
    if producers:
        query = query.filter(models.Component.producer.in_(producers))
    
    if status:
        if not joined_software_link:
            query = query.join(
                models.Software_Component_Link,
                models.Component.id == models.Software_Component_Link.component_id
            )
            joined_software_link = True
        if not joined_software:
            query = query.join(
                models.Software,
                models.Software_Component_Link.software_id == models.Software.id
            )
            joined_software = True
        query = query.filter(models.Software.status.in_(status))
    
    results = query.all()
    
    return [
        {"id": r.id, "name": r.name} 
        for r in results 
        if r.name is not None
    ]

def get_component_producers(
    db: Session,
    trac_model: List[str] = None,
    type_comp: List[str] = None,
    component_models: List[str] = None,
    status: List[str] = None
):
    """
    Получает уникальных производителей компонентов с учётом фильтров.
    Возвращает список словарей: [{'producer': 'Bosch'}, ...]
    
    Args:
        db: Сессия базы данных
        trac_model: Фильтр по моделям тракторов
        type_comp: Фильтр по типам компонентов
        component_models: Фильтр по моделям компонентов
        status: Фильтр по статусу ПО
        
    Returns:
        Список словарей с именами производителей
    """
    query = db.query(
        models.Component.producer
    ).distinct()
    
    joined_tractor_link = False
    joined_software_link = False
    joined_software = False
    
    # if trac_model:
    #     if not joined_software_link:
    #         query = query.join(
    #             models.Software_Component_Link,
    #             models.Component.id == models.Software_Component_Link.component_id
    #         )
    #         joined_software_link = True
    #     if not joined_tractor_link:
    #         query = query.join(
    #             models.Tractor_Software_And_Component_Link,
    #             models.Software_Component_Link.id == models.Tractor_Software_And_Component_Link.soft_comp_link_id
    #         )
    #         joined_tractor_link = True
    #     query = query.join(
    #         models.Tractor,
    #         models.Tractor_Software_And_Component_Link.tractor_id == models.Tractor.id
    #     )
    #     query = query.filter(models.Tractor.model.in_(trac_model))
    if trac_model:
        # Получаем все Software, у которых есть поле tractor_model
        software_records = db.query(models.Software).filter(
            models.Software.tractor_model.isnot(None)
        ).all()
        
        valid_software_ids = set()
        for sw in software_records:
            # Используем импортированную функцию
            models_list = _deserialize_tractor_models(sw.tractor_model)
            if any(m in models_list for m in trac_model):
                valid_software_ids.add(sw.id)
        
        # Применяем фильтр к Software_Component_Link
        if not joined_software_link:
            query = query.join(
                models.Software_Component_Link,
                models.Component.id == models.Software_Component_Link.component_id
            )
            joined_software_link = True
        query = query.filter(
            models.Software_Component_Link.software_id.in_(valid_software_ids)
        )
    
    if type_comp:
        query = query.filter(models.Component.type.in_(type_comp))
    
    if component_models:
        query = query.filter(models.Component.name.in_(component_models))
    
    if status:
        if not joined_software_link:
            query = query.join(
                models.Software_Component_Link,
                models.Component.id == models.Software_Component_Link.component_id
            )
            joined_software_link = True
        if not joined_software:
            query = query.join(
                models.Software,
                models.Software_Component_Link.software_id == models.Software.id
            )
            joined_software = True
        query = query.filter(models.Software.status.in_(status))
    
    results = query.all()
    
    return [
        {"producer": r.producer} 
        for r in results 
        if r.producer is not None
    ]
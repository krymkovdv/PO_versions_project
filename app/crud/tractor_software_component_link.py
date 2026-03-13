from sqlalchemy.orm import Session
from sqlalchemy import select
from .. import models, schemas
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# ============================================
# GET (Получение)
# ============================================
def get_all_tractor_software_component_links(db: Session):
    """Получить все связи Трактор ↔ ПО ↔ Компонент"""
    stmt = select(models.Tractor_Software_And_Component_Link)
    result = db.execute(stmt).scalars().all()
    return result

def get_tractor_software_component_link_by_id(db: Session, link_id: int):
    """Получить связь по ID"""
    return db.query(models.Tractor_Software_And_Component_Link).filter(
        models.Tractor_Software_And_Component_Link.id == link_id
    ).first()

def get_tractor_software_component_link_by_ids(
    db: Session, 
    tractor_id: int, 
    soft_comp_link_id: int
):
    """Получить связь по ID трактора и связи ПО-Компонент"""
    return db.query(models.Tractor_Software_And_Component_Link).filter(
        models.Tractor_Software_And_Component_Link.tractor_id == tractor_id,
        models.Tractor_Software_And_Component_Link.soft_comp_link_id == soft_comp_link_id
    ).first()

def get_links_by_tractor_id(db: Session, tractor_id: int):
    """Получить все связи для трактора"""
    return db.query(models.Tractor_Software_And_Component_Link).filter(
        models.Tractor_Software_And_Component_Link.tractor_id == tractor_id
    ).all()

def get_links_by_soft_comp_link_id(db: Session, soft_comp_link_id: int):
    """Получить все связи для связи ПО-Компонент"""
    return db.query(models.Tractor_Software_And_Component_Link).filter(
        models.Tractor_Software_And_Component_Link.soft_comp_link_id == soft_comp_link_id
    ).all()

def get_links_by_vin(db: Session, vin: str):
    """Получить все связи для трактора по VIN"""
    tractor = db.query(models.Tractor).filter(models.Tractor.vin == vin).first()
    if not tractor:
        return []
    return get_links_by_tractor_id(db, tractor.id)

# ============================================
# CREATE (Создание)
# ============================================
def create_tractor_software_component_link(
    db: Session, 
    link: schemas.TractorSoftwareComponentLinkCreate
):
    """Создать новую связь Трактор ↔ ПО ↔ Компонент"""
    
    # Проверка на дубликат
    existing = get_tractor_software_component_link_by_ids(
        db, 
        link.tractor_id, 
        link.soft_comp_link_id
    )
    if existing:
        raise ValueError(
            f"Link already exists for tractor_id={link.tractor_id}, "
            f"soft_comp_link_id={link.soft_comp_link_id}"
        )
    
    # Проверка существования трактора
    tractor = db.query(models.Tractor).filter(models.Tractor.id == link.tractor_id).first()
    if not tractor:
        raise ValueError(f"Tractor with id={link.tractor_id} not found")
    
    # Проверка существования связи ПО-Компонент
    soft_comp_link = db.query(models.Software_Component_Link).filter(
        models.Software_Component_Link.id == link.soft_comp_link_id
    ).first()
    if not soft_comp_link:
        raise ValueError(f"Software_Component_Link with id={link.soft_comp_link_id} not found")
    
    db_link = models.Tractor_Software_And_Component_Link(
        is_recom=link.is_recom,
        tractor_id=link.tractor_id,
        soft_comp_link_id=link.soft_comp_link_id
    )
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

# ============================================
# UPDATE (Обновление)
# ============================================
def update_tractor_software_component_link(
    db: Session, 
    link_id: int, 
    link_update: schemas.TractorSoftwareComponentLinkUpdate
):
    """Обновить связь Трактор ↔ ПО ↔ Компонент"""
    
    db_link = get_tractor_software_component_link_by_id(db, link_id)
    if not db_link:
        return None
    
    update_data = link_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(db_link, field):
            setattr(db_link, field, value)
    
    db.commit()
    db.refresh(db_link)
    return db_link

# ============================================
# DELETE (Удаление)
# ============================================
def delete_tractor_software_component_link(db: Session, link_id: int):
    """Удалить связь Трактор ↔ ПО ↔ Компонент"""
    
    db_link = get_tractor_software_component_link_by_id(db, link_id)
    if not db_link:
        return False
    
    db.delete(db_link)
    db.commit()
    return True

def delete_tractor_software_component_link_by_ids(
    db: Session, 
    tractor_id: int, 
    soft_comp_link_id: int
):
    """Удалить связь по ID трактора и связи ПО-Компонент"""
    
    db_link = get_tractor_software_component_link_by_ids(db, tractor_id, soft_comp_link_id)
    if not db_link:
        return False
    
    db.delete(db_link)
    db.commit()
    return True

def delete_all_links_by_tractor_id(db: Session, tractor_id: int):
    """Удалить все связи для трактора"""
    links = get_links_by_tractor_id(db, tractor_id)
    for link in links:
        db.delete(link)
    db.commit()
    return len(links)

# ============================================
# HELPER (Вспомогательные функции)
# ============================================
def get_tractors_for_software_component(db: Session, soft_comp_link_id: int):
    """Получить все тракторы для связи ПО-Компонент"""
    links = get_links_by_soft_comp_link_id(db, soft_comp_link_id)
    return [link.tractor for link in links]

def get_software_components_for_tractor(db: Session, tractor_id: int):
    """Получить все связи ПО-Компонент для трактора"""
    links = get_links_by_tractor_id(db, tractor_id)
    return [link.software_Component_Link for link in links]

def link_exists(db: Session, tractor_id: int, soft_comp_link_id: int) -> bool:
    """Проверить, существует ли связь"""
    link = get_tractor_software_component_link_by_ids(db, tractor_id, soft_comp_link_id)
    return link is not None

def get_recommended_software_for_tractor(db: Session, tractor_id: int):
    """Получить рекомендованное ПО для трактора"""
    links = db.query(models.Tractor_Software_And_Component_Link).filter(
        models.Tractor_Software_And_Component_Link.tractor_id == tractor_id,
        models.Tractor_Software_And_Component_Link.is_recom == True
    ).all()
    return [link.software_Component_Link for link in links]

# ============================================
# Расширенные запросы с JOIN
# ============================================
def get_tractor_software_with_details(db: Session, tractor_id: int):
    """Получить связи с подробной информацией о тракторе, ПО и компоненте"""
    query = db.query(
        models.Tractor_Software_And_Component_Link.id,
        models.Tractor.vin.label('tractor_vin'),
        models.Tractor.model.label('tractor_model'),
        models.Software.id.label('software_id'),
        models.Software.path.label('software_path'),
        models.Component.id.label('component_id'),
        models.Component.type.label('component_type'),
        models.Component.name.label('component_name'),
        models.Tractor_Software_And_Component_Link.is_recom
    ).select_from(models.Tractor_Software_And_Component_Link)\
    .join(models.Tractor, models.Tractor_Software_And_Component_Link.tractor_id == models.Tractor.id)\
    .join(models.Software_Component_Link, models.Tractor_Software_And_Component_Link.soft_comp_link_id == models.Software_Component_Link.id)\
    .join(models.Software, models.Software_Component_Link.software_id == models.Software.id)\
    .join(models.Component, models.Software_Component_Link.component_id == models.Component.id)\
    .filter(models.Tractor_Software_And_Component_Link.tractor_id == tractor_id)
    
    results = query.all()
    return [
        {
            'id': r.id,
            'tractor_vin': r.tractor_vin,
            'tractor_model': r.tractor_model,
            'software_id': r.software_id,
            'software_path': r.software_path,
            'component_id': r.component_id,
            'component_type': r.component_type,
            'component_name': r.component_name,
            'is_recom': r.is_recom
        }
        for r in results
    ]

def get_tractor_software_with_details_by_vin(db: Session, vin: str):
    """Получить связи с подробной информацией по VIN трактора"""
    tractor = db.query(models.Tractor).filter(models.Tractor.vin == vin).first()
    if not tractor:
        return []
    return get_tractor_software_with_details(db, tractor.id)
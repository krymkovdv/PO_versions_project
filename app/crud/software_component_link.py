from sqlalchemy.orm import Session
from sqlalchemy import select
from .. import models, schemas
from datetime import datetime, timezone

# ============================================
# GET (Получение)
# ============================================
def get_all_software_component_links(db: Session):
    """Получить все связи ПО ↔ Компонент"""
    stmt = select(models.Software_Component_Link)
    result = db.execute(stmt).scalars().all()
    return result

def get_software_component_link_by_id(db: Session, link_id: int):
    """Получить связь по ID"""
    return db.query(models.Software_Component_Link).filter(
        models.Software_Component_Link.id == link_id
    ).first()

def get_software_component_link_by_ids(
    db: Session, 
    component_id: int, 
    software_id: int
):
    """Получить связь по ID компонента и ПО"""
    return db.query(models.Software_Component_Link).filter(
        models.Software_Component_Link.component_id == component_id,
        models.Software_Component_Link.software_id == software_id
    ).first()

def get_links_by_component_id(db: Session, component_id: int):
    """Получить все связи для компонента"""
    return db.query(models.Software_Component_Link).filter(
        models.Software_Component_Link.component_id == component_id
    ).all()

def get_links_by_software_id(db: Session, software_id: int):
    """Получить все связи для ПО"""
    return db.query(models.Software_Component_Link).filter(
        models.Software_Component_Link.software_id == software_id
    ).all()

# ============================================
# CREATE (Создание)
# ============================================
def create_software_component_link(
    db: Session, 
    link: schemas.SoftwareComponentsSchema
):
    """Создать новую связь ПО ↔ Компонент"""
    
    # Проверка на дубликат
    existing = get_software_component_link_by_ids(
        db, 
        link.component_id, 
        link.software_id
    )
    if existing:
        raise ValueError(
            f"Link already exists for component_id={link.component_id}, "
            f"software_id={link.software_id}"
        )
    
    db_link = models.Software_Component_Link(
        component_id=link.component_id,
        software_id=link.software_id
    )
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

# ============================================
# UPDATE (Обновление)
# ============================================
def update_software_component_link(
    db: Session, 
    link_id: int, 
    link_update: schemas.SoftwareComponentLinkUpdate
):
    """Обновить связь ПО ↔ Компонент"""
    
    db_link = get_software_component_link_by_id(db, link_id)
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
def delete_software_component_link(db: Session, link_id: int):
    """Удалить связь ПО ↔ Компонент"""
    
    db_link = get_software_component_link_by_id(db, link_id)
    if not db_link:
        return False
    
    db.delete(db_link)
    db.commit()
    return True

def delete_software_component_link_by_ids(
    db: Session, 
    component_id: int, 
    software_id: int
):
    """Удалить связь по ID компонента и ПО"""
    
    db_link = get_software_component_link_by_ids(db, component_id, software_id)
    if not db_link:
        return False
    
    db.delete(db_link)
    db.commit()
    return True

# ============================================
# HELPER (Вспомогательные функции)
# ============================================
def get_components_for_software(db: Session, software_id: int):
    """Получить все компоненты для ПО"""
    links = get_links_by_software_id(db, software_id)
    return [link.component for link in links]

def get_software_for_component(db: Session, component_id: int):
    """Получить всё ПО для компонента"""
    links = get_links_by_component_id(db, component_id)
    return [link.software for link in links]

def link_exists(db: Session, component_id: int, software_id: int) -> bool:
    """Проверить, существует ли связь"""
    link = get_software_component_link_by_ids(db, component_id, software_id)
    return link is not None
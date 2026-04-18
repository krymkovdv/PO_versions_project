from sqlalchemy.orm import Session
from .. import models, schemas
from sqlalchemy import select
import logging
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from typing import List, Optional
from . import software
logger = logging.getLogger(__name__)

def get_tractors(db: Session):
    stmt = select(models.Tractor)
    result = db.execute(stmt).scalars().all()
    return result

def create_tractor(db: Session, tractor: schemas.TractorsSchema):
    db_tractor = models.Tractor(
        model=tractor.model,
        vin=tractor.vin,
        oh_hour=tractor.oh_hour,
        last_activity=tractor.last_activity,
        assembly_date=tractor.assembly_date,
        region=tractor.region,
        consumer=tractor.consumer,
        dealer=tractor.dealer
    )
    db.add(db_tractor)
    db.commit()
    db.refresh(db_tractor)
    return db_tractor

def get_tractor_by_id(db: Session, id: int):
    return db.query(models.Tractor).filter(models.Tractor.id == id).first()

def delete_tractor(db: Session, id: int):
    tractor = db.query(models.Tractor).filter(models.Tractor.id == id).first()
    if tractor is None:
        return False
    db.delete(tractor)
    db.commit()
    return True

def update_tractor(db: Session, vin: str, tractor_update: schemas.TractorUpdate):
    db_tractor = db.query(models.Tractor).filter(models.Tractor.vin == vin).first()
    if not db_tractor:
        raise HTTPException(status_code=404, detail="Tractor not found")
    for field, value in tractor_update.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(db_tractor, field, value)
    try:
        db.commit()
        db.refresh(db_tractor)
        return db_tractor
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Update failed due to integrity constraint")
    
def get_tractor_models_for_tractor_table(
    db: Session
):
    """
    Получает уникальные модели тракторов, связанные с компонентами/ПО.
    Возвращает список словарей: [{'model': 'K-7'}, ...]
    """
    query = db.query(
        models.Tractor.model
    ).distinct()
    results = query.all()
    
    return [
        {"model": r.model} 
        for r in results 
        if r.model is not None
    ]

def get_tractor_models_for_software_table(
    db: Session,
    component_types: Optional[List[str]] = None,
    component_models: Optional[List[str]] = None,
    component_producers: Optional[List[str]] = None,
    software_status: Optional[List[str]] = None
) -> List[dict]:
    """
    Получает уникальные модели тракторов из поля Software.tractor_model.
    
    Args:
        db: Сессия БД
        component_types: Фильтр по типам компонентов
        component_models: Фильтр по моделям компонентов  
        component_producers: Фильтр по производителям компонентов
        software_status: Фильтр по статусу ПО
        
    Returns:
        Список словарей: [{'model': 'K-7'}, {'model': 'K-525'}, ...]
    """
    # Базовый запрос к Software
    query = select(models.Software)
    
    #  Если нужны фильтры по компонентам — добавляем JOIN'ы
    if component_types or component_models or component_producers:
        query = (
            query
            .join(
                models.Software_Component_Link,
                models.Software.id == models.Software_Component_Link.software_id
            )
            .join(
                models.Component,
                models.Software_Component_Link.component_id == models.Component.id
            )
        )
        if component_types:
            query = query.filter(models.Component.type.in_(component_types))
        if component_models:
            query = query.filter(models.Component.name.in_(component_models))
        if component_producers:
            query = query.filter(models.Component.producer.in_(component_producers))
    
    #  Фильтр по статусу ПО
    if software_status:
        query = query.filter(models.Software.status.in_(software_status))
    
    #  Исключаем архивные записи (опционально)
    # query = query.filter(models.Software.is_archive == False)
    
    # Выполняем запрос
    software_records = db.execute(query).scalars().all()
    EXCLUDED_MODELS = {'default_model', 'кауау', 'ТЕСТ', 'K742MCT1', '{default_model}', '{K742MCT1}'}
    #  Собираем и десериализуем модели тракторов
    unique_models = set()
    for sw in software_records:
        models_list = software._deserialize_tractor_models(sw.tractor_model)
        for model in models_list:
            if model and isinstance(model, str):
                # Отбрасываем явный мусор
                if model in EXCLUDED_MODELS:
                    continue
                # Отбрасываем строки, содержащие default_model (даже внутри кавычек)
                if 'default_model' in model:
                    continue
                # Отбрасываем слишком длинные строки (признак вложенности)
                if len(model) > 100:
                    continue
                unique_models.add(model.strip())
    filtered_models = [m for m in unique_models if m not in EXCLUDED_MODELS]
    return [{"model": model} for model in sorted(filtered_models)]
    # Возвращаем в нужном формате
  
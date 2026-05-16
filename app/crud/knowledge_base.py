from sqlalchemy.orm import Session
from sqlalchemy import select
from .. import models

def get_knowledge_base(db: Session, type: str):
    stmt = select(models.KnowledgeBase).filter(models.KnowledgeBase.type == type)
    result = db.execute(stmt).scalars().all()
    return result
from sqlalchemy.orm import Session
from sqlalchemy import select
from .. import models
from fastapi import HTTPException, status, UploadFile
from datetime import datetime
import os
import shutil

def get_knowledge_base(db: Session, type: str):
    stmt = select(models.KnowledgeBase).filter(models.KnowledgeBase.type == type)
    result = db.execute(stmt).scalars().all()
    return result

KNOWLEDGE_BASE_DIR = "uploads/knowledge_base"

# def create_knowledge_base(
#     db: Session,
#     type: str,
#     file: UploadFile,
#     path: str = None
# ) -> models.KnowledgeBase:
#     """Создать запись в базе знаний с загрузкой файла"""
    
#     # 1. Создаём директорию если её нет
#     os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)
    
#     # 2. Генерируем уникальное имя файла
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     safe_filename = f"{timestamp}_{file.filename}"
#     file_path = os.path.join(KNOWLEDGE_BASE_DIR, safe_filename)
    
#     # 3. Сохраняем файл на диск
#     with open(file_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)
    
#     # 4. Сохраняем путь в БД
#     db_entry = models.KnowledgeBase(
#         type=type,
#         path=file_path  # путь к файлу на сервере
#     )
    
#     db.add(db_entry)
#     db.commit()
#     db.refresh(db_entry)
    
#     return db_entry
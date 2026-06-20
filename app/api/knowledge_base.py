from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from sqlalchemy.orm import Session
from ..crud.software import validate_tractor_models
from .. import schemas, crud, models
from ..database import get_session
from ..authorization import require_role, get_current_user
from ..log import logger
from typing import Optional, Union, List, Annotated
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import FileResponse, Response
from datetime import datetime
import os
import json
import shutil

router = APIRouter(prefix="/knowledge_base", tags=["KnowledgeBase"])


@router.get("", response_model=List[schemas.KnowledgeBase])
def get_knowledge_base(
    type: Optional[str] = None,  # ← добавьте параметр
    session: Session = Depends(get_session)
):
    return crud.knowledge_base.get_knowledge_base(session, type)

@router.post("/upload", status_code=201)
def upload_file(
    file: UploadFile = File(...),
    current_user = Depends(require_role("moderator"))
):
    # Создаём папку если нет
    os.makedirs("uploads/knowledge_base", exist_ok=True)
    
    # Генерируем уникальное имя
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join("uploads/knowledge_base", filename)
    
    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"path": file_path}


# 2. POST "" - сохранить путь в БД (JSON)
@router.post("", status_code=201)
def create_knowledge_base(
    data: schemas.KnowledgeBaseAdd,  # ← JSON с type и path
    db: Session = Depends(get_session),
    current_user = Depends(require_role("moderator"))
):
    db_entry = models.KnowledgeBase(
        type=data.type,
        path=data.path
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry


@router.get("/download/{file_id}")
def download_knowledge_base_file(
    file_id: int,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)  # любой авторизованный
):
    # Получаем запись из БД
    entry = db.query(models.KnowledgeBase).filter(models.KnowledgeBase.id == file_id).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Проверяем, существует ли файл
    if not os.path.exists(entry.path):
        raise HTTPException(status_code=404, detail="File not found on server")
    
    # Возвращаем файл
    return FileResponse(
        path=entry.path,
        filename=os.path.basename(entry.path),
        media_type="application/octet-stream"
    )

@router.delete("/{file_id}", status_code=204)
def delete_knowledge_base_file(
    file_id: int,
    db: Session = Depends(get_session),
    current_user = Depends(require_role("moderator"))
):
    # Получаем запись из БД
    entry = db.query(models.KnowledgeBase).filter(models.KnowledgeBase.id == file_id).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Удаляем физический файл (если существует)
    if entry.path and os.path.exists(entry.path):
        try:
            os.remove(entry.path)
            logger.info(f"Deleted file: {entry.path}")
        except OSError as e:
            logger.error(f"Error deleting file {entry.path}: {e}")
            # Продолжаем удаление записи из БД, даже если файл не удалился
    
    # Удаляем запись из БД
    db.delete(entry)
    db.commit()
    
    return Response(status_code=204)
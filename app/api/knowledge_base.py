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

router = APIRouter(prefix="/knowledge_base", tags=["KnowledgeBase"])


@router.get("", response_model=List[schemas.KnowledgeBase])
def get_knowledge_base(
    type: Optional[str] = None,  # ← добавьте параметр
    session: Session = Depends(get_session)
):
    return crud.knowledge_base.get_knowledge_base(session, type)

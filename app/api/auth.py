from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from ..database import get_session
from ..authorization import authenticate_user, create_access_token
from ..log import logger

router = APIRouter(prefix="/token", tags=["Token"])

@router.post("")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"[login] Неудачная попытка входа: username='{form_data.username}' — неверные учетные данные user=anonymous role=anonymous")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    logger.info(f"[login] Успешный вход username={user.username} role={user.role}")
    return {"access_token": access_token, "token_type": "bearer"}


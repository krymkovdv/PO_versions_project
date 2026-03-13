from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from sqlalchemy.orm import Session

from .. import schemas, crud, models
from ..database import get_session
from ..authorization import require_role, get_password_hash, get_current_user
from ..log import logger
from typing import List
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("", response_model=List[schemas.UserSchema])
def get_users(db: Session = Depends(get_session), current_user: models.UserDB = Depends(get_current_user)):
    try: 
        logger.info(f"[get_user] успешно выполнена user={current_user.username} role={current_user.role}")
        return crud.users.get_users(db)
    except SQLAlchemyError as e:
        logger.error(f"[get_user] ошибка SQLAlchemy {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении пользователей: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[get_user] неизвестная ошибка {str(e)} user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )
    
@router.post("", status_code=201, dependencies=[Depends(require_role("moderator"))])
def post_user(user: schemas.UserCreate, db: Session = Depends(get_session), current_user: models.UserDB = Depends(get_current_user)):
    existing = db.query(models.UserDB).filter(models.UserDB.username == user.username).first()
    if existing:
        logger.info(f"[post_user] команда успешно выполнена user={current_user.username} role={current_user.role}")
        raise HTTPException(status_code=409, detail="User already exists")
    user_in = models.UserDB(
        username=user.username,
        password_hash=get_password_hash(user.password),
        role=user.role
    )
    db.add(user_in)
    db.commit()
    db.refresh(user_in)
    logger.info(f"[post_user] создан пользователь {user_in.username} user={current_user.username} role={current_user.role}")
    return {"username": user_in.username, "role": user_in.role}

@router.delete("", dependencies=[Depends(require_role("moderator"))])
def delete_user(id: int, db: Session = Depends(get_session), current_user: models.UserDB = Depends(get_current_user)):
    if crud.users.delete_users(db, id):
        logger.info(f"[delete_users] выполнена успешно user={current_user.username} role={current_user.role}")
        return {"message": f"User {id} deleted successfully"}
    else:
        logger.error(f"[delete_users] неизвестная ошибка user={current_user.username} role={current_user.role}", exc_info=True)
        raise HTTPException(status_code=404, detail="User not found")
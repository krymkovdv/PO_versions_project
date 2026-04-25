from sqlalchemy.orm import Session
from .. import models, schemas, authorization
from fastapi import HTTPException
import logging
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError


logger = logging.getLogger(__name__)

def get_users(db: Session):
    stmt = select(models.UserDB)
    result = db.execute(stmt).scalars().all()
    return result

def create_user(db: Session, user: schemas.UserCreate):
    existing = db.query(models.UserDB).filter(models.UserDB.username == user.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")
    user_in = models.UserDB(
        username=user.username,
        password_hash= authorization.get_password_hash(user.password),
        role=user.role
    )
    db.add(user_in)
    try:
        db.commit()
        db.refresh(user_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="User already exists")
    return {"username": user_in.username, "role": user_in.role}

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    """
    Обновляет данные пользователя.
    Если передан пароль - хеширует его.
    Проверяет уникальность username, если он меняется.
    """
    db_user = db.query(models.UserDB).filter(models.UserDB.id == user_id).first()
    if not db_user:
        return None

    # Подготовка данных для обновления
    update_data = user_update.model_dump(exclude_unset=True)

    # Если меняется username, проверяем, не занят ли он другим пользователем
    if "username" in update_data and update_data["username"] != db_user.username:
        existing = db.query(models.UserDB).filter(
            models.UserDB.username == update_data["username"]
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Username already exists")

    # Если передан пароль, хешируем его перед сохранением
    if "password" in update_data and update_data["password"]:
        update_data["password_hash"] = authorization.get_password_hash(update_data.pop("password"))

    # Применяем обновления
    for field, value in update_data.items():
        if hasattr(db_user, field):
            setattr(db_user, field, value)

    try:
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Conflict while updating user")
    
    # Возвращаем объект модели (он автоматически сериализуется схемой в роутере)
    return db_user
def delete_users(db: Session, id: int):
    user = db.query(models.UserDB).filter(models.UserDB.id == id).first()
    if user is None:
        return False
    db.delete(user)
    db.commit()
    return True

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

def delete_users(db: Session, id: int):
    user = db.query(models.UserDB).filter(models.UserDB.id == id).first()
    if user is None:
        return False
    db.delete(user)
    db.commit()
    return True
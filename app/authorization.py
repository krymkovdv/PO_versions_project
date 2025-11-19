from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from .config import settings
from .database import get_session
from .models import UserDB
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
import logging

logger = logging.getLogger(__name__)
# Хэширование пароля    
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({
        "exp": expire,
        "role": data.get("role")  # передавать роль сюда
    })
    auth_data = settings.get_auth_data()
    return jwt.encode(to_encode, auth_data['secret_key'], algorithm=auth_data['algorithm'])

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return False
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(
            token, 
            settings.get_auth_data()['secret_key'],  # ← лучше брать из auth_data, как в create_access_token
            algorithms=[settings.get_auth_data()['algorithm']]
        )
        username = payload.get("sub")
        token_role = payload.get("role")  # роль из токена
        if username is None or token_role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if user is None:
        raise credentials_exception
    if token_role != user.role:
        logger.warning(f"Role mismatch for user {username}: token={token_role}, db={user.role}")
        raise credentials_exception  # или HTTP 401
    return user  # не нужно user.role = role — она и так правильная из БД

def require_role(*allowed_roles: str):
    def role_checker(user: UserDB = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: one of {list(allowed_roles)}. Got: '{user.role}'"
            )
        return user
    return role_checker
from .models import Base
from pydantic import Field
from enum import Enum
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = "b1a09b4adc807b8200624aa212acbc9b28ebb60a13540ea1f74185be52205af8"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30







class UserRole(str, Enum):
    ENGINEER = "engineer"
    DILLER = "diller"
    MODERATOR = "moderator"

class UserCreate(Base):
    login: str = Field(max_lenght=32, min_lenght=5)
    password: str = Field(max_lenght=32, min_lenght=5)
    role: UserRole = UserRole.ENGINEER

class Token(Base):
    acess_token: str
    token_type: str = 'engineer'


class User(Base):
    login: str
    role: UserRole

# Хэширование пароля    
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


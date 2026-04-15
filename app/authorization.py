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
from ldap3 import Server, Connection, ALL
from ldap3.core.exceptions import LDAPException
from ldap3.utils.conv import escape_filter_chars

logger = logging.getLogger(__name__)

# Контекст для хэширования паролей с использованием bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Схема OAuth2 для получения токена по URL "/token"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_password_hash(password: str) -> str:
    """
    Хэширование пароля с использованием bcrypt
    
    Args:
        password: оригинальный пароль
        
    Returns:
        захэшированный пароль
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверка соответствия введенного пароля хэшированному значению
    
    Args:
        plain_password: введенный пользователем пароль
        hashed_password: сохраненный в базе хэш пароля
        
    Returns:
        True если пароли совпадают, иначе False
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    """
    Создание JWT токена доступа
    
    Args:
        data: словарь с данными для включения в токен (обычно username и role)
        
    Returns:
        закодированный JWT токен, действителен 30 дней
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)  # Токен действителен 30 дней
    to_encode.update({
        "exp": expire,  # время истечения токена
        "role": data.get("role")  # роль пользователя из переданных данных
    })
    auth_data = settings.get_auth_data()
    return jwt.encode(to_encode, auth_data['secret_key'], algorithm=auth_data['algorithm'])

def authenticate_user(db: Session, username: str, password: str):
    """
    Аутентификация пользователя по имени и паролю
    
    Args:
        db: сессия базы данных
        username: имя пользователя
        password: введенный пароль
        
    Returns:
        объект пользователя если аутентификация успешна, иначе False
    """
    try:
        # Поиск пользователя в базе данных по имени
        user = db.query(UserDB).filter(UserDB.username == username).first()
        # Проверка соответствия пароля хэшу
        if not user or not verify_password(password, user.password_hash):
            return False
        return user
    except Exception:
        logger.error(f"[authenticate_user] Ошибка при аутентификации: ", exc_info=True)
        return False

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_session)):
    """
    Получение текущего аутентифицированного пользователя из токена
    
    Args:
        token: JWT токен из заголовка Authorization
        db: сессия базы данных
        
    Returns:
        объект пользователя если токен валиден, иначе выбрасывает HTTPException
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )
    try:
        # Декодирование токена для получения данных пользователя
        payload = jwt.decode(
            token, 
            settings.get_auth_data()['secret_key'],  # секретный ключ из конфигурации
            algorithms=[settings.get_auth_data()['algorithm']]  # алгоритм из конфигурации
        )
        username = payload.get("sub")  # имя пользователя из токена
        token_role = payload.get("role")  # роль пользователя из токена
        if username is None or token_role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    # Поиск пользователя в базе данных
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if user is None:
        raise credentials_exception
    # Проверка соответствия роли в токене и в базе данных
    if token_role != user.role:
        logger.warning(f"Role mismatch for user {username}: token={token_role}, db={user.role}")
        raise credentials_exception
    return user

def require_role(*allowed_roles: str):
    """
    Декоратор для проверки роли пользователя
    
    Args:
        *allowed_roles: список разрешенных ролей
        
    Returns:
        функцию-проверку, которая проверяет роль текущего пользователя
    """
    def role_checker(user: UserDB = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: one of {list(allowed_roles)}. Got: '{user.role}'"
            )
        return user
    return role_checker

def extract_user_and_role_from_token(token: str) -> tuple[str, str]:
    """
    Извлечение имени пользователя и роли из токена без проверки сессии базы данных
    
    Args:
        token: JWT токен
        
    Returns:
        кортеж (имя пользователя, роль) или ("anonymous", "anonymous") в случае ошибки
    """
    try:
        auth_data = settings.get_auth_data()
        payload = jwt.decode(
            token,
            auth_data['secret_key'],
            algorithms=[auth_data['algorithm']]
        )
        username = payload.get("sub", "anonymous")
        role = payload.get("role", "anonymous")
        return username, role
    except JWTError:
        return "anonymous", "anonymous"

def LDAP_AUTH(
    domain: str,
    username: str,
    password: str,
    base_dn: str | None = None,
    user_filter: str | None = None,
) -> bool:
    """ авторизация в LDAP

    :param domain: домен
    :param username: авторизующийся пользователь
    :param password: пароль пользователя
    :return: bool
    """
    can_auth = False
    conn = None
    try:
        if not username or not password:
            return False

        # Bind под credentials пользователя: LDAP сам подтверждает или отклоняет логин.
        server = Server(f"ldap://{domain}", get_info=ALL, connect_timeout=5)
        conn = Connection(
            server,
            user=f"{username}@{domain}",
            password=password,
            auto_bind=True,
            receive_timeout=5,
        )
        can_auth = True

        # Опциональная дополнительная проверка: пользователь существует и активен по LDAP-фильтру.
        if base_dn and user_filter:
            escaped_username = escape_filter_chars(username)
            base_filter = user_filter.format(username=escaped_username)
            if "{username}" in user_filter:
                search_filter = base_filter
            else:
                # Если в шаблоне нет {username}, добавляем фильтр по sAMAccountName автоматически.
                search_filter = f"(&{base_filter}(sAMAccountName={escaped_username}))"
            can_auth = conn.search(
                search_base=base_dn,
                search_filter=search_filter,
                attributes=["cn"],
                size_limit=1,
            ) and len(conn.entries) > 0
    except LDAPException as err:
        logger.warning("[LDAP_AUTH] LDAP error for user %s: %s", username, err)
    except Exception:
        logger.error("[LDAP_AUTH] Unexpected error", exc_info=True)
    finally:
        # Закрываем соединение в любом случае.
        try:
            if conn:
                conn.unbind()
        except Exception:
            logger.error("[LDAP_AUTH] Failed to unbind LDAP connection", exc_info=True)
    return can_auth


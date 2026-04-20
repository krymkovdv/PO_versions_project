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
import socket
from ldap3 import Server, Connection, ALL
from ldap3.core.exceptions import LDAPException
from ldap3.utils.conv import escape_filter_chars
from urllib.parse import urlparse

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
    server_address: str | None = None,
    port: int | None = None,
    use_ssl: bool | None = None,
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

    def parse_ldap_target(raw_address: str) -> tuple[str, int | None, bool]:
        """Нормализуем LDAP адрес: поддерживаем host, host:port, ldap://host[:port], ldaps://host[:port]."""
        value = (raw_address or "").strip()
        if not value:
            return "", None, False

        if "://" in value:
            parsed = urlparse(value)
            host = parsed.hostname or ""
            parsed_port = parsed.port
            parsed_ssl = parsed.scheme.lower() == "ldaps"
            return host, parsed_port, parsed_ssl

        host = value
        parsed_port = None
        if ":" in value:
            candidate_host, candidate_port = value.rsplit(":", 1)
            if candidate_port.isdigit():
                host = candidate_host
                parsed_port = int(candidate_port)
        return host.strip(), parsed_port, False

    try:
        if not username or not password:
            return False

        ldap_target = server_address or domain
        server_host, parsed_port, parsed_ssl = parse_ldap_target(ldap_target)
        if not server_host:
            logger.warning("[LDAP_AUTH] LDAP server address is empty or invalid")
            return False

        effective_port = port if port is not None else parsed_port
        effective_ssl = use_ssl if use_ssl is not None else parsed_ssl
        resolved_port = effective_port or (636 if effective_ssl else 389)

        # Быстрый precheck DNS/адреса, чтобы в логах было ясно, что именно не так с host.
        try:
            socket.getaddrinfo(server_host, resolved_port)
        except OSError as resolve_err:
            logger.warning(
                "[LDAP_AUTH] LDAP host is not resolvable/reachable: host=%s port=%s error=%s",
                server_host,
                resolved_port,
                resolve_err,
            )
            return False

        # Bind под credentials пользователя: LDAP сам подтверждает или отклоняет логин.
        server = Server(
            server_host,
            port=effective_port,
            use_ssl=effective_ssl,
            get_info=ALL,
            connect_timeout=5,
        )

        raw_username = username.strip()
        sam_account_name = raw_username
        if "\\" in sam_account_name:
            sam_account_name = sam_account_name.split("\\")[-1]
        if "@" in sam_account_name:
            sam_account_name = sam_account_name.split("@", 1)[0]

        candidate_users: list[str] = []

        def add_candidate(value: str) -> None:
            candidate = (value or "").strip()
            if candidate and candidate not in candidate_users:
                candidate_users.append(candidate)

        add_candidate(raw_username)
        if domain:
            add_candidate(f"{sam_account_name}@{domain}")
            netbios_domain = domain.split(".", 1)[0].upper()
            add_candidate(f"{netbios_domain}\\{sam_account_name}")

        bind_error_details = ""
        bound_user = ""

        for candidate_user in candidate_users:
            current_conn = Connection(
                server,
                user=candidate_user,
                password=password,
                auto_bind=False,
                receive_timeout=5,
            )
            if current_conn.bind():
                conn = current_conn
                can_auth = True
                bound_user = candidate_user
                break

            result = current_conn.result or {}
            bind_error_details = (
                f"description={result.get('description')} "
                f"message={result.get('message')} "
                f"code={result.get('result')}"
            )
            try:
                current_conn.unbind()
            except Exception:
                logger.error("[LDAP_AUTH] Failed to unbind LDAP connection", exc_info=True)

        if not can_auth:
            logger.warning(
                "[LDAP_AUTH] LDAP bind rejected for user %s: host=%s port=%s ssl=%s tried=%s details=%s",
                username,
                server_host,
                resolved_port,
                effective_ssl,
                candidate_users,
                bind_error_details or "n/a",
            )
            return False

        # Опциональная дополнительная проверка выполняется только
        # если фильтр явно привязан к конкретному username через {username}.
        if base_dn and user_filter and "{username}" in user_filter:
            filter_username = sam_account_name if sam_account_name else bound_user
            escaped_username = escape_filter_chars(filter_username)
            search_filter = user_filter.format(username=escaped_username)
            can_auth = conn.search(
                search_base=base_dn,
                search_filter=search_filter,
                attributes=["cn"],
                size_limit=1,
            ) and len(conn.entries) > 0
    except LDAPException as err:
        logger.warning(
            "[LDAP_AUTH] LDAP error for user %s: host=%s port=%s ssl=%s error=%s",
            username,
            server_host if 'server_host' in locals() else 'unknown',
            resolved_port if 'resolved_port' in locals() else 'unknown',
            effective_ssl if 'effective_ssl' in locals() else 'unknown',
            err,
        )
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


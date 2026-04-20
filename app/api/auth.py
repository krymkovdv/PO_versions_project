from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from ..database import get_session
from ..authorization import authenticate_user, create_access_token, LDAP_AUTH, get_password_hash
from ..config import settings
from ..models import UserDB
from ..log import logger
from ..crud.users import create_user
from ..schemas import UserCreate

router = APIRouter(prefix="/token", tags=["Token"])

@router.post("")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    username = form_data.username.strip()

    if settings.ldap_enabled:
        if not (settings.ldap_server or settings.ldap_domain):
            logger.error("[login] LDAP включен, но не задан LDAP_SERVER или LDAP_DOMAIN")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="LDAP is not configured")

        ldap_ok = LDAP_AUTH(
            domain=settings.ldap_domain,
            username=username,
            password=form_data.password,
            server_address=settings.ldap_server,
            port=settings.ldap_port,
            use_ssl=settings.ldap_use_ssl,
            base_dn=settings.ldap_base_dn or None,
            user_filter=settings.ldap_user_filter or None,
        )
        if not ldap_ok:
            logger.warning(f"[login] LDAP reject: username='{username}' user=anonymous role=anonymous")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

        # После успешного bind роль берем из локальной БД.
        user = db.query(UserDB).filter(UserDB.username == username).first()
        if not user:
            if settings.ldap_auto_provision:
                # Автоматически создаем пользователя с дефолтной ролью при первом логине.
                try:
                    new_user = UserCreate(
                        username=username,
                        password="LDAP_AUTHENTICATED",  # Пароль не используется, т.к. проверка через LDAP
                        role=settings.ldap_default_role
                    )
                    create_user(db, new_user)
                    user = db.query(UserDB).filter(UserDB.username == username).first()
                    logger.info(f"[login] LDAP user provisioned: username='{username}' role='{settings.ldap_default_role}'")
                except Exception as e:
                    logger.error(f"[login] Failed to provision LDAP user: username='{username}' error={e}")
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to provision user")
            else:
                logger.warning(f"[login] LDAP ok, but local user not found and auto-provision disabled: username='{username}' user=anonymous role=anonymous")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not provisioned in local database")
    else:
        user = authenticate_user(db, username, form_data.password)
        if not user:
            logger.warning(f"[login] Неудачная попытка входа: username='{username}' — неверные учетные данные user=anonymous role=anonymous")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    logger.info(f"[login] Успешный вход username={user.username} role={user.role}")
    return {"access_token": access_token, "token_type": "bearer"}


from typing import ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    """Класс настроек приложения, загружаемых из файла .env"""
    
    # Параметры подключения к базе данных
    db_host: str           # Хост базы данных
    db_port: int           # Порт базы данных
    db_user: str           # Имя пользователя базы данных
    db_password: str       # Пароль пользователя базы данных
    db_name: str           # Имя базы данных
    
    # Параметры аутентификации
    secret_key: str        # Секретный ключ для подписи JWT токенов
    algorithm: str         # Алгоритм шифрования JWT токенов
    access_token_expire_minutes: int  # Время жизни токена в минутах

    # LDAP авторизация
    ldap_enabled: bool = False
    ldap_domain: str = ""
    ldap_server: str = ""
    ldap_port: int | None = None
    ldap_use_ssl: bool = False
    ldap_base_dn: str = ""
    ldap_user_filter: str = "(&(objectClass=user)(objectCategory=Person)(!(userAccountControl:1.2.840.113556.1.4.803:=2))(sAMAccountName={username}))"
    ldap_auto_provision: bool = True
    ldap_default_role: str = "dealer"

    # Путь к файлу .env
    env_path: ClassVar[str] = os.path.join(os.path.dirname(__file__), '.env')
    
    # Конфигурация для загрузки настроек из .env файла
    model_config = SettingsConfigDict(env_file=env_path)

    def get_url(self):
        """Метод для генерации строки подключения к базе данных PostgreSQL"""
        return f'postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}'

    def get_auth_data(self):
        """Метод для получения данных аутентификации (секретный ключ и алгоритм)"""
        return {"secret_key": self.secret_key, "algorithm": self.algorithm}

# Глобальный экземпляр настроек
settings = Settings()

# Параметры для загрузки файлов
UPLOAD_DIR = "uploads/firmware"              # Директория для загрузки прошивок
MAX_FILE_SIZE = 100 * 1024 * 1024 * 1024    # Максимальный размер файла (100 ГБ)
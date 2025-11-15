from typing import ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    env_path: ClassVar[str] = os.path.join(os.path.dirname(__file__), '.env')
    model_config = SettingsConfigDict(env_file=env_path)

    def get_url(self):
        return f'postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}'

    def get_auth_data(self):
        return {"secret_key": self.secret_key, "algorithm": self.algorithm}

settings = Settings()

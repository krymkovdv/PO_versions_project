class Settings:
    DB_HOST = "localhost"
    DB_PORT = 5432
    DB_USER = "postgres"
    DB_PASSWORD = "123123"
    DB_NAME = "postgres"
    def get_url(self):
        return f'postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}'

    def get_auth_data(self):
        return {"secret_key": self.secret_key, "algorithm": self.algorithm}

settings = Settings()

UPLOAD_DIR = "uploads/firmware"
MAX_FILE_SIZE = 1024 * 1024 * 1024
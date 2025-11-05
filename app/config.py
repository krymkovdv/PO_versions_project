class Settings:
    DB_HOST = "10.100.16.187"
    DB_PORT = 5432
    DB_USER = "postuser"
    DB_PASSWORD = "qwert123"
    DB_NAME = "test"
    def get_url(self):
        return f'postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

settings = Settings()
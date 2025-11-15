class Settings:
    DB_HOST="10.100.16.187"
    DB_PORT="5433"
    DB_USER="user"
    DB_PASSWORD="root"
    DB_NAME="postgres"
    def get_url(self):
        return f'postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

settings = Settings()
from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SMTPConfig(BaseSettings):
    server: str = "smtp_server"
    port: int = 587
    username: str = "smtp_user"
    password: str = "smtp_password"


class Settings(BaseSettings):
    JWT_ALGORITHM: str
    JWT_EXPIRE: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_DB: str

    APP_NAME: str = "MyApp"
    ENV: str = "development"
    DEBUG: bool = False
    PORT: int = 8000

    EMAIL_SERVER: str = "smtp_server"
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: str = "smtp_user"
    EMAIL_PASSWORD: str = "smtp_password"

    @computed_field
    @property
    def DATABASE_URL(self) -> PostgresDsn:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}/{self.POSTGRES_DB}"

    @computed_field
    @property
    def ASYNC_DATABASE_URL(self) -> PostgresDsn:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()

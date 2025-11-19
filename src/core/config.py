from typing import Optional
from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SMTPConfig(BaseSettings):
    server: str
    port: int
    username: str
    password: str


class Settings(BaseSettings):

    JWT_ALGORITHM: str
    JWT_EXPIRE: int
    SECRET_KEY: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_DB: str

    APP_NAME: str
    ENV: str
    DEBUG: bool
    PORT: int

    EMAIL_SERVER: str
    EMAIL_PORT: int
    EMAIL_USERNAME: str
    EMAIL_PASSWORD: str

    FERNET_KEY: str
    VERIFICATION_BASE_URL: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    FCM_SERVER_KEY: Optional[str] = None
    SICK_LEAVE_LIMIT: int = 10
    CASUAL_LEAVE_LIMIT: int = 10

    AUTH_BASE: str = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL: str = "https://oauth2.googleapis.com/token"
    GMAIL_SEND_SCOPE: str = "https://www.googleapis.com/auth/gmail.send"

    @computed_field
    @property
    def DATABASE_URL(self) -> PostgresDsn:
        """Sync DB URL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}/{self.POSTGRES_DB}"

    @computed_field
    @property
    def ASYNC_DATABASE_URL(self) -> PostgresDsn:
        """Async DB URL"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, env_file_encoding="utf-8"
    )


settings = Settings()

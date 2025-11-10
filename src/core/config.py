import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    ENV: str = os.getenv("ENV", "development")
    DEBUG: str = os.getenv("DEBUG", "false").lower() == "true"
    ASYNC_DATABASE_URL: str = os.getenv("ASYNC_DATABASE_URL")

settings = Settings()

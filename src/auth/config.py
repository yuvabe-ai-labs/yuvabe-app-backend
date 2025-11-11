import os
from pydantic import BaseSettings
from dotenv import load_dotenv


class HomeSettings(BaseSettings):
    FEATURE_ENABLED: bool = True


home_settings = HomeSettings()


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

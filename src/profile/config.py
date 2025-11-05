from pydantic import BaseSettings

class HomeSettings(BaseSettings):
    FEATURE_ENABLED: bool = True

home_settings = HomeSettings()
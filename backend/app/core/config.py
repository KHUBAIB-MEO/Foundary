from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Values with "=" have a default. DATABASE_URL has none, so it is required.
    PROJECT_NAME: str = "Foundary"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    DATABASE_URL: str

    # Read the values from the .env file. Ignore any extra keys inside it.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# One shared object. Other files do: from app.core.config import settings
settings = Settings()
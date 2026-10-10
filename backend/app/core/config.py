from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Values with "=" have a default. DATABASE_URL has none, so it is required.
    PROJECT_NAME: str = "Foundary"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    DATABASE_URL: str

    # Read the values from the .env file. Ignore any extra keys inside it.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


    # --- Security ---
    SECRET_KEY: str  # used to sign tokens.
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    VERIFY_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # --- Email ---
    EMAIL_BACKEND: str = "console"  
    EMAIL_FROM: str = "no-reply@foundary.local"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""


# One shared object. Other files do: from app.core.config import settings
settings = Settings()
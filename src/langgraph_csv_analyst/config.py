from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Model Settings
    DEFAULT_MODEL: str = "deepseek-chat"
    DEFAULT_TEMPERATURE: float = 0.0

    # OpenAI API Configuration
    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str = "https://api.deepseek.com"

    # CSV Processing Limits
    CSV_MAX_SIZE_MB: int = 50
    MAX_ROWS_DISPLAY: int = 100

    # Application Settings
    APP_NAME: str = "LangGraph CSV Analyst"
    DEBUG: bool = False

    # API Server Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()

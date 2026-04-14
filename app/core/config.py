from pydantic_settings import BaseSettings, SettingsConfigDict


CUSTOM_GMAIL_LABELS: list[str] = [
    "action_needed",
    "fyi",
    "unimportant",
    "predicted_spam",
]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "FastAPI Demo"
    debug: bool = True
    database_url: str = "sqlite:///./app.db"

    # Gmail
    google_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )


settings = Settings()

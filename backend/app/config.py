from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    mongodb_uri: str = ""
    db_name: str = "simly_orbis"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-haiku-20241022"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Don't raise an error for missing fields – we handle missing URI ourselves.
        extra="ignore",
    )


# Singleton instance imported everywhere else.
settings = Settings()

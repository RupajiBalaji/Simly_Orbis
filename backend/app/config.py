from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    mongodb_uri: str = ""
    db_name: str = "simly_orbis"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-lite-latest"

    # RC1 Hardening & Cost Protection
    mentor_daily_cap: int = 300
    ai_enabled: bool = True
    allowed_origins: str = "*"
    trust_proxy: bool = False
    git_sha: str = ""
    app_version: str = "0.2.0-dev"

    model_config = SettingsConfigDict(
        env_file=("backend/.env", ".env"),
        env_file_encoding="utf-8",
        # Don't raise an error for missing fields – we handle missing URI ourselves.
        extra="ignore",
    )


# Singleton instance imported everywhere else.
settings = Settings()

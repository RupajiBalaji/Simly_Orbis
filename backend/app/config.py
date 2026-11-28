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
    allowed_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    trust_proxy: bool = False
    git_sha: str = ""
    app_version: str = "0.9.0-dev"
    environment: str = "development"
    spec_runtime: bool = False

    # P6 Classroom, accounts, tokens & retention settings (13.4, 13.6)
    guest_session_retention_days: int = 90
    teacher_invite_ttl_minutes: int = 60
    teacher_session_ttl_hours: int = 24
    student_session_ttl_hours: int = 24
    join_code_ttl_days: int = 90
    admin_token: str = ""

    model_config = SettingsConfigDict(
        env_file=("backend/.env", ".env"),
        env_file_encoding="utf-8",
        # Don't raise an error for missing fields – we handle missing URI ourselves.
        extra="ignore",
    )


# Singleton instance imported everywhere else.
settings = Settings()

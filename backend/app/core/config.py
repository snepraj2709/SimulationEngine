from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_settings_override: "Settings | None" = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Decision Simulation Engine"
    app_version: str = "0.1.0"
    environment: Literal["development", "test", "staging", "production"] = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    frontend_base_url: str = "http://localhost:5173"
    database_url: str = "postgresql+psycopg://decision:decision@localhost:5432/decision_sim"
    jwt_secret_key: str = "change-me-to-a-32-char-secret-at-minimum"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )
    log_level: str = "INFO"
    analysis_cache_hours: int = 24
    request_timeout_seconds: float = 10.0
    connect_timeout_seconds: float = 5.0
    scrape_max_content_chars: int = 15000
    scrape_max_bytes: int = 2_000_000
    rate_limit_per_minute: int = 60
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.4"
    allow_private_network_scraping: bool = False
    demo_user_email: str = "demo@example.com"
    demo_user_password: str = "DemoPass123!"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return ["http://localhost:5173"]


@lru_cache(maxsize=1)
def _load_settings() -> Settings:
    return Settings()


def get_settings() -> Settings:
    return _settings_override or _load_settings()


def set_settings_override(settings: Settings | None) -> None:
    global _settings_override
    _settings_override = settings

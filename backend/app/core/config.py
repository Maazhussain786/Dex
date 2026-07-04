from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass(frozen=True)
class Settings:
    environment: str
    log_level: str
    api_host: str
    api_port: int
    cors_origins: list[str]


@lru_cache
def get_settings() -> Settings:
    cors_origins = os.getenv("DEX_CORS_ORIGINS", "http://localhost:3000")
    return Settings(
        environment=os.getenv("DEX_ENV", "development"),
        log_level=os.getenv("DEX_LOG_LEVEL", "INFO"),
        api_host=os.getenv("DEX_API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("DEX_API_PORT", "8000")),
        cors_origins=[origin.strip() for origin in cors_origins.split(",") if origin.strip()],
    )

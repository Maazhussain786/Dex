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

    # PostgreSQL
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str

    # Neo4j
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str

    # Qdrant
    qdrant_url: str

    @property
    def postgres_dsn(self) -> str:
        """Build a ``postgresql://`` DSN from individual fields."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    cors_origins = os.getenv("DEX_CORS_ORIGINS", "http://localhost:3000")
    return Settings(
        environment=os.getenv("DEX_ENV", "development"),
        log_level=os.getenv("DEX_LOG_LEVEL", "INFO"),
        api_host=os.getenv("DEX_API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("DEX_API_PORT", "8000")),
        cors_origins=[origin.strip() for origin in cors_origins.split(",") if origin.strip()],
        # PostgreSQL
        postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
        postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
        postgres_db=os.getenv("POSTGRES_DB", "dex"),
        postgres_user=os.getenv("POSTGRES_USER", "dex"),
        postgres_password=os.getenv("POSTGRES_PASSWORD", "dex"),
        # Neo4j
        neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
        neo4j_password=os.getenv("NEO4J_PASSWORD", "dex_password"),
        # Qdrant
        qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
    )

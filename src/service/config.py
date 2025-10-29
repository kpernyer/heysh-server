"""Configuration settings for the backend service.

Philosophy: Use hostnames (via Caddy), not port numbers.
Local development uses .env.local, production uses .env.production.
Same code works everywhere via smart configuration.
"""

import os

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings - hostname-based configuration.

    Defaults match .env.local (hostname-based via Caddy).
    Override with .env.production for production deployment.
    """

    # Environment
    environment: str = os.getenv("ENVIRONMENT", "local")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Core Application URLs
    api_url: str = os.getenv("API_URL", "http://api.hey.local")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://hey.local")

    # Temporal Workflow Engine
    temporal_address: str = os.getenv("TEMPORAL_ADDRESS", "temporal.hey.local:7233")
    temporal_namespace: str = os.getenv("TEMPORAL_NAMESPACE", "default")
    temporal_api_key: str = os.getenv("TEMPORAL_API_KEY", "")
    temporal_task_queue: str = os.getenv("TEMPORAL_TASK_QUEUE", "hey-sh-workflows")
    temporal_ui_url: str = os.getenv("TEMPORAL_UI_URL", "http://temporal.hey.local")

    # Business Database (abstracted - local Postgres or Supabase in production)
    database_url: str = os.getenv("DATABASE_URL", "postgresql://temporal:temporal@db.hey.local:5432/heysh")

    # Neo4j Graph Database
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://neo4j.hey.local:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password")
    neo4j_database: str = os.getenv("NEO4J_DATABASE", "neo4j")
    neo4j_browser_url: str = os.getenv("NEO4J_BROWSER_URL", "http://neo4j.hey.local")

    # Weaviate Vector Database
    weaviate_url: str = os.getenv("WEAVIATE_URL", "http://weaviate.hey.local")
    weaviate_api_key: str = os.getenv("WEAVIATE_API_KEY", "")

    # Temporal's Internal Database (used by Temporal service itself)
    postgres_url: str = os.getenv("POSTGRES_URL", "postgresql://temporal:temporal@db.hey.local:5432/temporal")

    # Supabase (provides Postgres and Storage in production)
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_KEY", "")

    # Document Storage (abstracted - MinIO locally, Supabase Storage in production)
    storage_url: str = os.getenv("STORAGE_URL", "http://storage.hey.local")
    storage_api_key: str = os.getenv("STORAGE_API_KEY", "")

    # MinIO (local storage implementation detail)
    minio_console_url: str = os.getenv("MINIO_CONSOLE_URL", "http://minio-console.hey.local")
    minio_root_user: str = os.getenv("MINIO_ROOT_USER", "minioadmin")
    minio_root_password: str = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")

    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://redis.hey.local:6379")

    # AI Service Keys
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Backend Service Configuration
    backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8002"))
    reload: bool = os.getenv("RELOAD", "true").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "debug")

    @property
    def is_local(self) -> bool:
        """Check if running in local environment."""
        return self.environment == "local"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def cors_origins(self) -> list[str]:
        """Get CORS origins based on environment.

        Returns:
            List of allowed CORS origins (hostname-based)
        """
        if self.is_local:
            return [
                "http://hey.local",
                "http://www.hey.local",
                self.frontend_url,
            ]
        else:
            return [
                "https://www.hey.sh",
                "https://hey.sh",
                self.frontend_url,
            ]

    model_config = ConfigDict(
        env_file=".env.local",  # Default to local
        env_file_encoding="utf-8",
    )


def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings instance with environment-specific configuration
    """
    return Settings()

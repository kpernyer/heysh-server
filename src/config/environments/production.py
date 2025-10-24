"""
Production environment configuration.
"""

from config.hostnames import HostnameConfig, Environment


class ProductionConfig(HostnameConfig):
    """Production environment configuration."""

    environment: Environment = Environment.PRODUCTION

    # Production hostnames
    app_hostname: str = "app.hey.sh"
    api_hostname: str = "api.hey.sh"

    # Production-specific settings
    debug: bool = False
    log_level: str = "INFO"
    auto_reload: bool = False

    # Production ports
    ports: dict = {
        "backend": 8000,
        "frontend": 3000,
        "temporal": 7233,
        "temporal_ui": 8080,
        "postgres": 5432,
        "redis": 6379,
        "grafana": 3000,
        "prometheus": 9090,
        "caddy_http": 80,
        "caddy_https": 443,
    }

    # Production service URLs
    backend_url: str = "http://backend-service:8000"
    frontend_url: str = "http://frontend-service:3000"
    temporal_url: str = "http://temporal-service:7233"
    postgres_url: str = "postgresql://user:password@postgres-service:5432/hey_sh"
    redis_url: str = "redis://redis-service:6379"

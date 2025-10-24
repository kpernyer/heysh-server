"""
Development environment configuration.
"""

from config.hostnames import HostnameConfig, Environment


class DevelopmentConfig(HostnameConfig):
    """Development environment configuration."""

    environment: Environment = Environment.DEVELOPMENT

    # Development hostnames
    app_hostname: str = "dev.hey.sh"
    api_hostname: str = "dev-api.hey.sh"

    # Development-specific settings
    debug: bool = True
    log_level: str = "DEBUG"
    auto_reload: bool = True

    # Development ports (different from production)
    dev_ports: dict = {
        "backend": 8001,
        "frontend": 3001,
        "temporal": 7233,
        "temporal_ui": 8081,
        "postgres": 5432,
        "redis": 6379,
        "grafana": 3002,
        "prometheus": 9091,
        "caddy_http": 80,
        "caddy_https": 443,
    }

    # Development service URLs
    backend_url: str = "http://backend-dev-service:8001"
    frontend_url: str = "http://frontend-dev-service:3001"
    temporal_url: str = "http://temporal-dev-service:7233"
    postgres_url: str = (
        "postgresql://user:password@postgres-dev-service:5432/hey_sh_dev"
    )
    redis_url: str = "redis://redis-dev-service:6379"

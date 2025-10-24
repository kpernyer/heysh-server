"""
Centralized hostname and port configuration.
All services must use these defined values to prevent conflicts.
"""

from typing import Dict
from pydantic import BaseModel, Field, validator
from enum import Enum


class Environment(str, Enum):
    """Environment enumeration."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class HostnameConfig(BaseModel):
    """Hostname and port configuration with strict validation."""

    # Environment
    environment: Environment = Field(
        default=Environment.DEVELOPMENT, description="Environment"
    )

    # Production hostnames
    app_hostname: str = Field(
        default="app.hey.sh", description="Main application hostname"
    )
    api_hostname: str = Field(default="api.hey.sh", description="API hostname")
    temporal_hostname: str = Field(
        default="temporal.hey.sh", description="Temporal UI hostname"
    )
    grafana_hostname: str = Field(
        default="grafana.hey.sh", description="Grafana hostname"
    )
    prometheus_hostname: str = Field(
        default="prometheus.hey.sh", description="Prometheus hostname"
    )

    # Development hostnames
    dev_app_hostname: str = Field(
        default="dev.hey.sh", description="Development app hostname"
    )
    dev_api_hostname: str = Field(
        default="dev-api.hey.sh", description="Development API hostname"
    )

    # Port allocation (strict to prevent conflicts)
    ports: Dict[str, int] = Field(
        default={
            "backend": 8000,
            "frontend": 3000,
            "temporal": 7233,
            "temporal_ui": 8080,
            "postgres": 5432,
            "redis": 6379,
            "grafana": 3002,
            "prometheus": 9090,
            "caddy_http": 80,
            "caddy_https": 443,
        },
        description="Port allocation for all services",
    )

    # Development ports (different from production)
    dev_ports: Dict[str, int] = Field(
        default={
            "backend": 8002,  # Changed to avoid conflict
            "frontend": 3004,  # Changed to avoid conflict
            "temporal": 7235,  # Changed to avoid conflict
            "temporal_ui": 8082,  # Changed to avoid conflict
            "postgres": 5434,  # Changed to avoid conflict
            "redis": 6381,  # Changed to avoid conflict
            "grafana": 3005,  # Changed to avoid conflict
            "prometheus": 9092,  # Changed to avoid conflict
            "caddy_http": 80,
            "caddy_https": 443,
        },
        description="Development port allocation",
    )

    # Service URLs
    backend_url: str = Field(
        default="http://backend-service:8000", description="Backend service URL"
    )
    frontend_url: str = Field(
        default="http://frontend-service:3000", description="Frontend service URL"
    )
    temporal_url: str = Field(
        default="http://temporal-service:7233", description="Temporal service URL"
    )
    postgres_url: str = Field(
        default="postgresql://user:password@postgres-service:5432/hey_sh",
        description="PostgreSQL URL",
    )
    redis_url: str = Field(
        default="redis://redis-service:6379", description="Redis URL"
    )

    @validator("ports", "dev_ports")
    def validate_ports(cls, v):
        """Validate that all ports are unique and within valid range."""
        port_values = list(v.values())

        # Check for duplicates
        if len(port_values) != len(set(port_values)):
            raise ValueError("All ports must be unique")

        # Check port range
        for service, port in v.items():
            if not (1024 <= port <= 65535):
                raise ValueError(
                    f"Port {port} for {service} must be between 1024 and 65535"
                )

        return v

    @validator("app_hostname", "api_hostname")
    def validate_hostnames(cls, v):
        """Validate hostname format."""
        if not v.endswith(".hey.sh"):
            raise ValueError(f"Hostname {v} must end with .hey.sh")
        return v

    def get_service_url(self, service: str) -> str:
        """Get service URL by name."""
        if service == "backend":
            return self.backend_url
        elif service == "frontend":
            return self.frontend_url
        elif service == "temporal":
            return self.temporal_url
        elif service == "postgres":
            return self.postgres_url
        elif service == "redis":
            return self.redis_url
        else:
            raise ValueError(f"Unknown service: {service}")

    def get_port(self, service: str) -> int:
        """Get port for service."""
        if self.environment == Environment.DEVELOPMENT:
            if service not in self.dev_ports:
                raise ValueError(f"Unknown service: {service}")
            return self.dev_ports[service]
        else:
            if service not in self.ports:
                raise ValueError(f"Unknown service: {service}")
            return self.ports[service]

    def get_hostname(self, service: str) -> str:
        """Get hostname for service."""
        if self.environment == Environment.DEVELOPMENT:
            if service == "app":
                return self.dev_app_hostname
            elif service == "api":
                return self.dev_api_hostname
        else:
            if service == "app":
                return self.app_hostname
            elif service == "api":
                return self.api_hostname

        # Monitoring services
        if service == "temporal":
            return self.temporal_hostname
        elif service == "grafana":
            return self.grafana_hostname
        elif service == "prometheus":
            return self.prometheus_hostname

        raise ValueError(f"Unknown service: {service}")

    class Config:
        env_prefix = "HEY_SH_"
        case_sensitive = False


# Global configuration instance
hostname_config = HostnameConfig()

"""
Hey.sh Configuration
Single source of truth for all environment-specific configuration.
"""

import os
from typing import Dict, Literal

# Environment detection
ENVIRONMENT: Literal["development", "production"] = os.getenv("HEY_ENV", "development")

# HTTPS mode for local development
USE_HTTPS_LOCAL = os.getenv("HEY_HTTPS", "false").lower() in ("true", "1", "yes")

# Base domains
DEV_DOMAIN = "hey.local"
PROD_DOMAIN = "hey.sh"

# Service names (consistent across environments)
SERVICES = {
    "frontend": "www.hey",
    "api": "api",
    "temporal": "temporal", 
    "temporal_ui": "temporal-ui",
    "neo4j": "neo4j",
    "weaviate": "weaviate",
    "postgres": "db",
    "redis": "redis",
    "minio": "minio",
    "monitoring": "monitoring",
    "grafana": "grafana",
    "alertmanager": "alertmanager",
    "jaeger": "jaeger",
    "loki": "loki",
}

# Ports (consistent across environments)
PORTS = {
    "api": 8002,
    "temporal": 7233,
    "temporal_ui": 8090,
    "neo4j": 7474,
    "weaviate": 8082,
    "postgres": 5432,
    "redis": 6379,
    "minio": 9000,
    "minio_console": 9001,
    "monitoring": 9090,
    "grafana": 3001,
    "alertmanager": 9093,
    "jaeger": 16686,
    "loki": 3100,
    "caddy_http": 80,
    "caddy_https": 443,
}

# Environment-specific configuration
class Config:
    """Single configuration class for all environments."""
    
    def __init__(self):
        self.environment = ENVIRONMENT
        self.is_development = self.environment == "development"
        self.is_production = self.environment == "production"
        
        # Choose domain based on environment
        self.domain = DEV_DOMAIN if self.is_development else PROD_DOMAIN
        
        # Choose protocol based on environment and HTTPS setting
        if self.is_production:
            self.protocol = "https"
        elif USE_HTTPS_LOCAL:
            self.protocol = "https"
        else:
            self.protocol = "http"
        
    def get_hostname(self, service: str) -> str:
        """Get full hostname for a service."""
        service_name = SERVICES.get(service)
        if not service_name:
            raise ValueError(f"Unknown service: {service}")
        
        # Special handling for frontend to use www.hey.local / www.hey.sh
        if service == "frontend":
            return f"www.{self.domain}"
        
        return f"{service_name}.{self.domain}"
    
    def get_url(self, service: str, path: str = "") -> str:
        """Get full URL for a service."""
        hostname = self.get_hostname(service)
        url = f"{self.protocol}://{hostname}"
        if path:
            url += f"/{path.lstrip('/')}"
        return url
    
    def get_port(self, service: str) -> int:
        """Get port for a service."""
        return PORTS.get(service, 80)
    
    def get_local_url(self, service: str, path: str = "") -> str:
        """Get localhost URL for a service (for direct access)."""
        port = self.get_port(service)
        url = f"http://localhost:{port}"
        if path:
            url += f"/{path.lstrip('/')}"
        return url

# Global configuration instance
config = Config()

# Convenience constants for easy importing
API_URL = config.get_url("api")
FRONTEND_URL = config.get_url("frontend")
TEMPORAL_URL = config.get_url("temporal")
TEMPORAL_UI_URL = config.get_url("temporal_ui")
NEO4J_URL = config.get_url("neo4j")
WEAVIATE_URL = config.get_url("weaviate")
POSTGRES_URL = config.get_url("postgres")
REDIS_URL = config.get_url("redis")
MINIO_URL = config.get_url("minio")
MONITORING_URL = config.get_url("monitoring")
GRAFANA_URL = config.get_url("grafana")
ALERTMANAGER_URL = config.get_url("alertmanager")
JAEGER_URL = config.get_url("jaeger")
LOKI_URL = config.get_url("loki")

# Local URLs for direct access
API_LOCAL_URL = config.get_local_url("api")
FRONTEND_LOCAL_URL = config.get_local_url("frontend")
TEMPORAL_LOCAL_URL = config.get_local_url("temporal")
TEMPORAL_UI_LOCAL_URL = config.get_local_url("temporal_ui")
NEO4J_LOCAL_URL = config.get_local_url("neo4j")
WEAVIATE_LOCAL_URL = config.get_local_url("weaviate")
POSTGRES_LOCAL_URL = config.get_local_url("postgres")
REDIS_LOCAL_URL = config.get_local_url("redis")
MINIO_LOCAL_URL = config.get_local_url("minio")
MONITORING_LOCAL_URL = config.get_local_url("monitoring")
GRAFANA_LOCAL_URL = config.get_local_url("grafana")
ALERTMANAGER_LOCAL_URL = config.get_local_url("alertmanager")
JAEGER_LOCAL_URL = config.get_local_url("jaeger")
LOKI_LOCAL_URL = config.get_local_url("loki")

# Environment info
ENVIRONMENT_INFO = {
    "environment": config.environment,
    "is_development": config.is_development,
    "is_production": config.is_production,
    "domain": config.domain,
    "protocol": config.protocol,
}

#!/usr/bin/env python3
"""
Generate Docker Compose configurations from centralized configuration.
This script uses the centralized hostname and port configuration to generate
Docker Compose files with the correct values.
"""

import sys
import os
import yaml
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.hostnames import hostname_config


def generate_docker_config():
    """Generate Docker Compose configuration from centralized config."""
    print("🐳 Generating Docker Compose configuration from centralized config...")

    # Get configuration values
    app_hostname = hostname_config.get_hostname("app")
    api_hostname = hostname_config.get_hostname("api")
    temporal_hostname = hostname_config.get_hostname("temporal")
    grafana_hostname = hostname_config.get_hostname("grafana")
    prometheus_hostname = hostname_config.get_hostname("prometheus")

    # Get port values
    backend_port = hostname_config.get_port("backend")
    frontend_port = hostname_config.get_port("frontend")
    temporal_port = hostname_config.get_port("temporal")
    temporal_ui_port = hostname_config.get_port("temporal_ui")
    grafana_port = hostname_config.get_port("grafana")
    prometheus_port = hostname_config.get_port("prometheus")
    postgres_port = hostname_config.get_port("postgres")
    redis_port = hostname_config.get_port("redis")

    # Generate development Docker Compose
    dev_compose = {
        "version": "3.8",
        "services": {
            "caddy": {
                "image": "caddy:2-alpine",
                "container_name": "hey-caddy",
                "restart": "unless-stopped",
                "ports": ["80:80", "443:443"],
                "volumes": [
                    "./Caddyfile:/etc/caddy/Caddyfile",
                    "caddy_data:/data",
                    "caddy_config:/config",
                ],
                "networks": ["hey-network"],
                "healthcheck": {
                    "test": [
                        "CMD",
                        "caddy",
                        "health-check",
                        "--config",
                        "/etc/caddy/Caddyfile",
                    ],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3,
                },
            },
            "frontend": {
                "build": {"context": ".", "dockerfile": "Dockerfile.dev"},
                "container_name": "hey-frontend",
                "restart": "unless-stopped",
                "volumes": [".:/app", "/app/node_modules"],
                "environment": {
                    "VITE_SUPABASE_URL": "${VITE_SUPABASE_URL}",
                    "VITE_SUPABASE_ANON_KEY": "${VITE_SUPABASE_ANON_KEY}",
                    "VITE_TEMPORAL_ADDRESS": f"temporal:{temporal_port}",
                    "VITE_TEMPORAL_NAMESPACE": "default",
                    "VITE_API_URL": f"https://{api_hostname}",
                },
                "command": f"pnpm run dev --host 0.0.0.0 --port {frontend_port}",
                "networks": ["hey-network"],
                "healthcheck": {
                    "test": ["CMD", "curl", "-f", f"http://localhost:{frontend_port}"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3,
                },
            },
            "backend": {
                "build": {"context": "./backend", "dockerfile": "Dockerfile.dev"},
                "container_name": "hey-backend",
                "restart": "unless-stopped",
                "volumes": ["./backend:/app"],
                "environment": {
                    "DATABASE_URL": f"postgresql://hey_user:hey_password@postgres:{postgres_port}/hey_db_dev",
                    "NEO4J_URI": "bolt://neo4j:7687",
                    "NEO4J_USER": "neo4j",
                    "NEO4J_PASSWORD": "password",
                    "WEAVIATE_URL": "http://weaviate:8080",
                    "TEMPORAL_HOST": "temporal",
                    "TEMPORAL_PORT": str(temporal_port),
                    "ENVIRONMENT": "development",
                },
                "command": f"uv run uvicorn app.main:app --reload --host 0.0.0.0 --port {backend_port}",
                "depends_on": ["postgres", "neo4j", "weaviate", "temporal"],
                "networks": ["hey-network"],
                "healthcheck": {
                    "test": [
                        "CMD",
                        "curl",
                        "-f",
                        f"http://localhost:{backend_port}/health",
                    ],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3,
                },
            },
            "postgres": {
                "image": "postgres:15-alpine",
                "container_name": "hey-postgres",
                "restart": "unless-stopped",
                "environment": {
                    "POSTGRES_USER": "hey_user",
                    "POSTGRES_PASSWORD": "hey_password",
                    "POSTGRES_DB": "hey_db_dev",
                },
                "volumes": ["postgres_data:/var/lib/postgresql/data"],
                "networks": ["hey-network"],
                "healthcheck": {
                    "test": ["CMD-SHELL", "pg_isready -U hey_user -d hey_db_dev"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3,
                },
            },
            "temporal": {
                "image": "temporalio/auto-setup:latest",
                "container_name": "hey-temporal",
                "restart": "unless-stopped",
                "environment": {
                    "DB": "postgresql",
                    "DB_PORT": str(postgres_port),
                    "POSTGRES_USER": "hey_user",
                    "POSTGRES_PWD": "hey_password",
                    "POSTGRES_SEEDS": "postgres",
                },
                "volumes": ["./temporal-config:/etc/temporal/config/dynamicconfig"],
                "depends_on": ["postgres"],
                "networks": ["hey-network"],
                "healthcheck": {
                    "test": [
                        "CMD",
                        "temporal",
                        "workflow",
                        "list",
                        "--address",
                        f"localhost:{temporal_port}",
                    ],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3,
                },
            },
            "temporal-ui": {
                "image": "temporalio/ui:latest",
                "container_name": "hey-temporal-ui",
                "restart": "unless-stopped",
                "environment": {
                    "TEMPORAL_ADDRESS": f"temporal:{temporal_port}",
                    "TEMPORAL_CORS_ORIGINS": f"https://{app_hostname},https://{api_hostname}",
                },
                "depends_on": ["temporal"],
                "networks": ["hey-network"],
                "healthcheck": {
                    "test": [
                        "CMD",
                        "curl",
                        "-f",
                        f"http://localhost:{temporal_ui_port}",
                    ],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3,
                },
            },
            "grafana": {
                "image": "grafana/grafana:latest",
                "container_name": "hey-grafana",
                "restart": "unless-stopped",
                "environment": {
                    "GF_SECURITY_ADMIN_PASSWORD": "admin",
                    "GF_USERS_ALLOW_SIGN_UP": "false",
                },
                "volumes": ["grafana_data:/var/lib/grafana"],
                "networks": ["hey-network"],
                "healthcheck": {
                    "test": ["CMD", "curl", "-f", f"http://localhost:{grafana_port}"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3,
                },
            },
            "prometheus": {
                "image": "prom/prometheus:latest",
                "container_name": "hey-prometheus",
                "restart": "unless-stopped",
                "volumes": [
                    "prometheus_data:/prometheus",
                    "./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml",
                ],
                "command": [
                    "--config.file=/etc/prometheus/prometheus.yml",
                    "--storage.tsdb.path=/prometheus",
                    "--web.console.libraries=/etc/prometheus/console_libraries",
                    "--web.console.templates=/etc/prometheus/consoles",
                    "--web.enable-lifecycle",
                ],
                "networks": ["hey-network"],
                "healthcheck": {
                    "test": [
                        "CMD",
                        "curl",
                        "-f",
                        f"http://localhost:{prometheus_port}",
                    ],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3,
                },
            },
        },
        "volumes": {
            "caddy_data": {},
            "caddy_config": {},
            "postgres_data": {},
            "grafana_data": {},
            "prometheus_data": {},
        },
        "networks": {"hey-network": {"driver": "bridge"}},
    }

    # Write development Docker Compose
    docker_dir = Path("docker/generated")
    docker_dir.mkdir(parents=True, exist_ok=True)

    with open(docker_dir / "docker-compose.dev.yml", "w") as f:
        yaml.dump(dev_compose, f, default_flow_style=False, sort_keys=False)

    print("✅ Docker Compose configuration generated")
    print(f"  Development: {docker_dir / 'docker-compose.dev.yml'}")
    print(f"  Hostnames: {app_hostname}, {api_hostname}, {temporal_hostname}")
    print(
        f"  Ports: Frontend={frontend_port}, Backend={backend_port}, Temporal={temporal_port}"
    )


if __name__ == "__main__":
    generate_docker_config()

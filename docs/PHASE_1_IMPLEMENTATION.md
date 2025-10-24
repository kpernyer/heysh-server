# Phase 1: Configuration Centralization Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing Phase 1 of the codebase standards plan, focusing on configuration centralization and Caddy hostname management.

## Step 1: Create Centralized Configuration System

### 1.1 Create Configuration Directory Structure

```bash
# Create the configuration structure
mkdir -p config/environments
mkdir -p config/constants
mkdir -p config/validation

# Create __init__.py files
touch config/__init__.py
touch config/environments/__init__.py
touch config/constants/__init__.py
touch config/validation/__init__.py
```

### 1.2 Create Centralized Hostname Configuration

**File: `config/hostnames.py`**

```python
"""
Centralized hostname and port configuration.
All services must use these defined values to prevent conflicts.
"""

from typing import Dict, Set
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum
import os

class Environment(str, Enum):
    """Environment enumeration."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class HostnameConfig(BaseModel):
    """Hostname and port configuration with strict validation."""

    # Environment
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="Environment")

    # Production hostnames
    app_hostname: str = Field(default="app.hey.sh", description="Main application hostname")
    api_hostname: str = Field(default="api.hey.sh", description="API hostname")
    temporal_hostname: str = Field(default="temporal.hey.sh", description="Temporal UI hostname")
    grafana_hostname: str = Field(default="grafana.hey.sh", description="Grafana hostname")
    prometheus_hostname: str = Field(default="prometheus.hey.sh", description="Prometheus hostname")

    # Development hostnames
    dev_app_hostname: str = Field(default="dev.hey.sh", description="Development app hostname")
    dev_api_hostname: str = Field(default="dev-api.hey.sh", description="Development API hostname")

    # Port allocation (strict to prevent conflicts)
    ports: Dict[str, int] = Field(
        default={
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
        },
        description="Port allocation for all services"
    )

    # Development ports (different from production)
    dev_ports: Dict[str, int] = Field(
        default={
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
        },
        description="Development port allocation"
    )

    # Service URLs
    backend_url: str = Field(default="http://backend-service:8000", description="Backend service URL")
    frontend_url: str = Field(default="http://frontend-service:3000", description="Frontend service URL")
    temporal_url: str = Field(default="http://temporal-service:7233", description="Temporal service URL")
    postgres_url: str = Field(default="postgresql://user:password@postgres-service:5432/hey_sh", description="PostgreSQL URL")
    redis_url: str = Field(default="redis://redis-service:6379", description="Redis URL")

    @validator('ports', 'dev_ports')
    def validate_ports(cls, v):
        """Validate that all ports are unique and within valid range."""
        port_values = list(v.values())

        # Check for duplicates
        if len(port_values) != len(set(port_values)):
            raise ValueError('All ports must be unique')

        # Check port range
        for service, port in v.items():
            if not (1024 <= port <= 65535):
                raise ValueError(f'Port {port} for {service} must be between 1024 and 65535')

        return v

    @validator('app_hostname', 'api_hostname')
    def validate_hostnames(cls, v):
        """Validate hostname format."""
        if not v.endswith('.hey.sh'):
            raise ValueError(f'Hostname {v} must end with .hey.sh')
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
            raise ValueError(f'Unknown service: {service}')

    def get_port(self, service: str) -> int:
        """Get port for service."""
        if self.environment == Environment.DEVELOPMENT:
            if service not in self.dev_ports:
                raise ValueError(f'Unknown service: {service}')
            return self.dev_ports[service]
        else:
            if service not in self.ports:
                raise ValueError(f'Unknown service: {service}')
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

        raise ValueError(f'Unknown service: {service}')

    class Config:
        env_prefix = "HEY_SH_"
        case_sensitive = False

# Global configuration instance
hostname_config = HostnameConfig()
```

### 1.3 Create Constants Configuration

**File: `config/constants.py`**

```python
"""
Application constants and text strings.
All text strings and constants should be defined here.
"""

class Constants:
    """Application constants and text strings."""

    # API Endpoints
    API_BASE_URL = "https://api.hey.sh"
    GRAPHQL_ENDPOINT = "/graphql"
    HEALTH_CHECK_ENDPOINT = "/health"

    # Workflow Status
    WORKFLOW_STATUS_PENDING = "pending"
    WORKFLOW_STATUS_RUNNING = "running"
    WORKFLOW_STATUS_COMPLETED = "completed"
    WORKFLOW_STATUS_FAILED = "failed"
    WORKFLOW_STATUS_CANCELLED = "cancelled"

    # Error Messages
    ERROR_INVALID_WORKFLOW = "Invalid workflow definition"
    ERROR_MISSING_REQUIRED_FIELD = "Missing required field: {field}"
    ERROR_VALIDATION_FAILED = "Validation failed: {details}"
    ERROR_PORT_CONFLICT = "Port conflict detected: {ports}"
    ERROR_HOSTNAME_INVALID = "Invalid hostname format: {hostname}"

    # UI Messages
    SUCCESS_WORKFLOW_SAVED = "Workflow saved successfully"
    SUCCESS_DOCUMENT_UPLOADED = "Document uploaded successfully"
    INFO_PROCESSING_WORKFLOW = "Processing workflow..."
    INFO_SERVICE_STARTING = "Starting {service} service..."
    INFO_SERVICE_STOPPED = "Stopped {service} service"

    # Development Messages
    DEV_SERVICE_READY = "Development service ready at {url}"
    DEV_ALL_SERVICES_READY = "All development services ready"
    DEV_ACCESS_POINTS = "Access points:"
    DEV_FRONTEND = "Frontend: {url}"
    DEV_API = "API: {url}"
    DEV_TEMPORAL = "Temporal: {url}"

    # Health Check Messages
    HEALTH_CHECK_SUCCESS = "Health check passed"
    HEALTH_CHECK_FAILED = "Health check failed"
    HEALTH_CHECK_SERVICE_DOWN = "Service {service} is down"

    # Configuration Messages
    CONFIG_LOADED = "Configuration loaded for environment: {env}"
    CONFIG_VALIDATION_FAILED = "Configuration validation failed: {errors}"
    CONFIG_ENVIRONMENT_SET = "Environment set to: {env}"

    # Docker Messages
    DOCKER_SERVICES_STARTING = "Starting Docker services..."
    DOCKER_SERVICES_STOPPED = "Docker services stopped"
    DOCKER_SERVICES_RESTARTED = "Docker services restarted"
    DOCKER_CLEANUP_COMPLETE = "Docker cleanup completed"

    # Caddy Messages
    CADDY_STARTING = "Starting Caddy reverse proxy..."
    CADDY_STOPPED = "Caddy reverse proxy stopped"
    CADDY_RELOADED = "Caddy configuration reloaded"
    CADDY_VALIDATION_PASSED = "Caddy configuration is valid"
    CADDY_VALIDATION_FAILED = "Caddy configuration validation failed"

    # Database Messages
    DATABASE_CONNECTED = "Database connected successfully"
    DATABASE_DISCONNECTED = "Database disconnected"
    DATABASE_MIGRATION_COMPLETE = "Database migration completed"
    DATABASE_ROLLBACK_COMPLETE = "Database rollback completed"

    # Temporal Messages
    TEMPORAL_SERVER_STARTING = "Starting Temporal server..."
    TEMPORAL_SERVER_STARTED = "Temporal server started"
    TEMPORAL_WORKFLOW_STARTED = "Workflow {workflow_id} started"
    TEMPORAL_WORKFLOW_COMPLETED = "Workflow {workflow_id} completed"
    TEMPORAL_WORKFLOW_FAILED = "Workflow {workflow_id} failed"

    # Monitoring Messages
    MONITORING_STACK_STARTING = "Starting monitoring stack..."
    MONITORING_STACK_READY = "Monitoring stack ready"
    METRICS_COLLECTION_STARTED = "Metrics collection started"
    ALERTING_CONFIGURED = "Alerting configured"

    # Security Messages
    SECURITY_SCAN_STARTED = "Security scan started"
    SECURITY_SCAN_COMPLETED = "Security scan completed"
    SECURITY_VULNERABILITIES_FOUND = "Security vulnerabilities found: {count}"
    SECURITY_SCAN_CLEAN = "Security scan clean - no vulnerabilities found"

    # Testing Messages
    TESTS_STARTING = "Starting tests..."
    TESTS_COMPLETED = "Tests completed"
    TESTS_FAILED = "Tests failed: {failures}"
    TEST_COVERAGE = "Test coverage: {coverage}%"

    # Linting Messages
    LINTING_STARTED = "Running code quality checks..."
    LINTING_COMPLETED = "Code quality checks completed"
    LINTING_FAILED = "Code quality checks failed: {issues}"
    LINTING_CLEAN = "Code quality checks passed"

    # Deployment Messages
    DEPLOYMENT_STARTING = "Starting deployment..."
    DEPLOYMENT_COMPLETED = "Deployment completed successfully"
    DEPLOYMENT_FAILED = "Deployment failed: {error}"
    DEPLOYMENT_ROLLBACK = "Deployment rollback initiated"

    # Documentation Messages
    DOCS_GENERATING = "Generating documentation..."
    DOCS_GENERATED = "Documentation generated successfully"
    DOCS_VALIDATION_FAILED = "Documentation validation failed"
    DOCS_UPDATED = "Documentation updated"
```

### 1.4 Create Environment-Specific Configurations

**File: `config/environments/development.py`**

```python
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
    postgres_url: str = "postgresql://user:password@postgres-dev-service:5432/hey_sh_dev"
    redis_url: str = "redis://redis-dev-service:6379"
```

**File: `config/environments/production.py`**

```python
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
```

## Step 2: Update Caddyfile for Real Hostnames

### 2.1 Create New Caddyfile

**File: `Caddyfile`**

```caddyfile
# Global configuration
{
    # Enable automatic HTTPS for production
    email admin@hey.sh
    # Use Let's Encrypt for SSL certificates
    acme_ca https://acme-v02.api.letsencrypt.org/directory
}

# Production hostnames
app.hey.sh {
    # Frontend application
    reverse_proxy frontend-service:3000 {
        header_up Host {host}
        header_up X-Real-IP {remote}
        header_up X-Forwarded-For {remote}
        header_up X-Forwarded-Proto {scheme}
    }

    # Enable compression
    encode gzip

    # Security headers
    header {
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
        X-XSS-Protection "1; mode=block"
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
    }
}

# API backend
api.hey.sh {
    # Backend API
    reverse_proxy backend-service:8000 {
        header_up Host {host}
        header_up X-Real-IP {remote}
        header_up X-Forwarded-For {remote}
        header_up X-Forwarded-Proto {scheme}
    }

    # CORS configuration
    @cors_preflight method OPTIONS
    header @cors_preflight Access-Control-Allow-Origin "*"
    header @cors_preflight Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS"
    header @cors_preflight Access-Control-Allow-Headers "Content-Type, Authorization"

    # API rate limiting
    rate_limit {
        zone static {
            key {remote_host}
            events 100
            window 1m
        }
    }

    # Enable compression
    encode gzip

    # Security headers
    header {
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
        X-XSS-Protection "1; mode=block"
    }
}

# Temporal UI
temporal.hey.sh {
    # Temporal Web UI
    reverse_proxy temporal-service:8080 {
        header_up Host {host}
        header_up X-Real-IP {remote}
        header_up X-Forwarded-For {remote}
        header_up X-Forwarded-Proto {scheme}
    }

    # Basic authentication for Temporal UI
    basicauth {
        temporal $2a$14$encrypted_password_here
    }
}

# Monitoring and observability
grafana.hey.sh {
    # Grafana dashboard
    reverse_proxy grafana-service:3000 {
        header_up Host {host}
        header_up X-Real-IP {remote}
        header_up X-Forwarded-For {remote}
        header_up X-Forwarded-Proto {scheme}
    }

    # Basic authentication for Grafana
    basicauth {
        admin $2a$14$encrypted_password_here
    }
}

# Prometheus metrics
prometheus.hey.sh {
    # Prometheus server
    reverse_proxy prometheus-service:9090 {
        header_up Host {host}
        header_up X-Real-IP {remote}
        header_up X-Forwarded-For {remote}
        header_up X-Forwarded-Proto {scheme}
    }

    # Basic authentication for Prometheus
    basicauth {
        prometheus $2a$14$encrypted_password_here
    }
}

# Development environment
dev.hey.sh {
    # Development frontend
    reverse_proxy frontend-dev-service:3001 {
        header_up Host {host}
        header_up X-Real-IP {remote}
        header_up X-Forwarded-For {remote}
        header_up X-Forwarded-Proto {scheme}
    }
}

dev-api.hey.sh {
    # Development backend
    reverse_proxy backend-dev-service:8001 {
        header_up Host {host}
        header_up X-Real-IP {remote}
        header_up X-Forwarded-For {remote}
        header_up X-Forwarded-Proto {scheme}
    }
}
```

## Step 3: Update Justfile for Centralized Configuration

### 3.1 Update Justfile Commands

**File: `justfile`**

```justfile
# hey.sh development commands

# Show all available commands
default:
    @just --list

# Development setup
setup: setup-backend setup-frontend
    @echo ""
    @echo "✓ All environments configured!"
    @echo ""
    @echo "Next steps:"
    @echo "1. Update /etc/hosts (run: just hosts-setup)"
    @echo "2. Configure environment variables (cp .env.example .env.local)"
    @echo "3. Start services (just dev)"

# Setup Python environment
setup-backend:
    @echo "Setting up Python environment..."
    @cd backend && \
    if [ ! -d ".venv" ]; then \
        echo "  Creating venv..."; \
        python3.12 -m venv .venv; \
        echo "  Ensuring pip is available..."; \
        .venv/bin/python3 -m ensurepip --upgrade > /dev/null 2>&1 || true; \
    fi && \
    echo "  Installing dependencies..." && \
    .venv/bin/python3 -m pip install --upgrade pip setuptools wheel -q && \
    .venv/bin/python3 -m pip install -e '.[dev]' -q && \
    echo "  ✓ Python $(python3.12 --version | cut -d' ' -f2) ready"

# Setup Node environment
setup-frontend:
    @echo "Setting up Node environment..."
    @if command -v pnpm &> /dev/null; then \
        echo "  Installing with pnpm..." && \
        pnpm install -q; \
    else \
        echo "  Installing with npm..." && \
        npm install; \
    fi
    @echo "  ✓ Node $(node --version) ready"

# Add local domain entries to /etc/hosts
hosts-setup:
    @echo "Adding local domain entries to /etc/hosts..."
    @echo "You may be prompted for your password (sudo required)"
    @echo ""
    @sudo sh -c 'echo "\n# hey.sh local development domains" >> /etc/hosts'
    @sudo sh -c 'echo "127.0.0.1 dev.hey.sh" >> /etc/hosts'
    @sudo sh -c 'echo "127.0.0.1 dev-api.hey.sh" >> /etc/hosts'
    @sudo sh -c 'echo "127.0.0.1 temporal.hey.sh" >> /etc/hosts'
    @sudo sh -c 'echo "127.0.0.1 grafana.hey.sh" >> /etc/hosts'
    @sudo sh -c 'echo "127.0.0.1 prometheus.hey.sh" >> /etc/hosts'
    @echo ""
    @echo "✓ Local domains configured"

# Remove local domain entries from /etc/hosts
hosts-cleanup:
    @echo "Removing local domain entries from /etc/hosts..."
    @sudo sed -i '' '/# hey.sh local development domains/d' /etc/hosts
    @sudo sed -i '' '/dev.hey.sh/d' /etc/hosts
    @sudo sed -i '' '/dev-api.hey.sh/d' /etc/hosts
    @sudo sed -i '' '/temporal.hey.sh/d' /etc/hosts
    @sudo sed -i '' '/grafana.hey.sh/d' /etc/hosts
    @sudo sed -i '' '/prometheus.hey.sh/d' /etc/hosts
    @echo "✓ Local domains removed"

# Start all services with Docker Compose
docker-up:
    @echo "Starting all services..."
    docker-compose -f docker-compose.dev.yml up -d
    @echo ""
    @echo "✓ Services started"
    @echo ""
    @echo "Access points:"
    @echo "  Frontend:       https://dev.hey.sh"
    @echo "  Backend API:    https://dev-api.hey.sh"
    @echo "  Temporal UI:    https://temporal.hey.sh"
    @echo "  Grafana:        https://grafana.hey.sh"
    @echo "  Prometheus:     https://prometheus.hey.sh"

# Stop all services
docker-down:
    @echo "Stopping all services..."
    docker-compose -f docker-compose.dev.yml down
    @echo "✓ Services stopped"

# Restart all services
docker-restart:
    @echo "Restarting all services..."
    docker-compose -f docker-compose.dev.yml restart
    @echo "✓ Services restarted"

# View logs from all services
docker-logs:
    docker-compose -f docker-compose.dev.yml logs -f

# View logs from specific service
docker-logs-service service:
    docker-compose -f docker-compose.dev.yml logs -f {{service}}

# Stop all services and remove volumes (clean slate)
docker-clean:
    @echo "Stopping services and removing volumes..."
    docker-compose -f docker-compose.dev.yml down -v
    @echo "✓ Services stopped and volumes removed"

# Start frontend development server (without Docker)
dev:
    pnpm run dev

# Start backend API server (without Docker)
dev-api:
    @cd backend && \
    if [ ! -d ".venv" ]; then \
        echo "Venv not found, creating..."; \
        python3.12 -m venv .venv; \
        .venv/bin/python3 -m ensurepip --upgrade > /dev/null 2>&1 || true; \
        .venv/bin/python3 -m pip install --upgrade pip setuptools wheel -q; \
        .venv/bin/python3 -m pip install -e '.[dev]' -q; \
    fi && \
    .venv/bin/python3 -m uvicorn service.api:app --reload --host 0.0.0.0 --port 8001

# Start both frontend and backend (run in separate terminals)
dev-both:
    @echo "Start these in separate terminals:"
    @echo "  Terminal 1: just dev"
    @echo "  Terminal 2: just dev-api"
    @echo ""
    @echo "Or use 'just dev-full' to start everything"

# Build frontend for production
build:
    pnpm run build

# Run frontend tests
test:
    pnpm run test

# Run linter
lint:
    pnpm run lint

# Run type checker
typecheck:
    pnpm run typecheck

# Start Caddy reverse proxy only
caddy-start:
    caddy start --config Caddyfile

# Stop Caddy reverse proxy
caddy-stop:
    caddy stop

# Reload Caddy configuration
caddy-reload:
    caddy reload --config Caddyfile

# Validate Caddy configuration
caddy-validate:
    caddy validate --config Caddyfile

# Full development environment (Docker + frontend + backend)
dev-full:
    @echo "Starting full development environment..."
    @just docker-up
    @echo ""
    @echo "Waiting for services to be ready..."
    @sleep 5
    @echo ""
    @echo "Next steps:"
    @echo "  Terminal 1: just dev      (frontend)"
    @echo "  Terminal 2: just dev-api  (backend)"
    @echo ""
    @echo "Access at:"
    @echo "  Frontend: https://dev.hey.sh"
    @echo "  API:      https://dev-api.hey.sh"

# Health check for all services
health-check:
    @echo "Checking service health..."
    @echo ""
    @echo "Frontend (dev.hey.sh):"
    @curl -s -o /dev/null -w "%{http_code}" https://dev.hey.sh || echo "Not running"
    @echo ""
    @echo "Backend API (dev-api.hey.sh):"
    @curl -s -o /dev/null -w "%{http_code}" https://dev-api.hey.sh/health || echo "Not running"
    @echo ""
    @echo "Temporal (temporal.hey.sh):"
    @curl -s -o /dev/null -w "%{http_code}" https://temporal.hey.sh || echo "Not running"
    @echo ""
    @echo "Grafana (grafana.hey.sh):"
    @curl -s -o /dev/null -w "%{http_code}" https://grafana.hey.sh || echo "Not running"
    @echo ""
    @echo "Prometheus (prometheus.hey.sh):"
    @curl -s -o /dev/null -w "%{http_code}" https://prometheus.hey.sh || echo "Not running"

# Show running containers
ps:
    docker-compose -f docker-compose.dev.yml ps

# Verify all environments are correct
verify:
    @echo "🔍 Verifying environments..."
    @echo ""
    @echo "Python:"
    @cd backend && \
    if [ -d ".venv" ]; then \
        . .venv/bin/activate && \
        echo "  ✓ Venv activated" && \
        echo "  Python: $(python --version)" && \
        echo "  Location: $(which python)"; \
    else \
        echo "  ✗ Venv not found (run: just setup-backend)"; \
    fi
    @echo ""
    @echo "Node:"
    @echo "  Node: $(node --version)" && \
    echo "  npm: $(npm --version)" && \
    if command -v pnpm &> /dev/null; then \
        echo "  pnpm: $(pnpm --version)"; \
    fi
    @echo ""
    @echo "✓ Ready to develop"

# Enter Python shell with venv activated
shell-python:
    @cd backend && \
    if [ ! -d ".venv" ]; then \
        echo "Creating venv..."; \
        python3.12 -m venv .venv && \
        .venv/bin/python3 -m ensurepip --upgrade > /dev/null 2>&1 || true && \
        .venv/bin/python3 -m pip install --upgrade pip setuptools wheel -q && \
        .venv/bin/python3 -m pip install -e '.[dev]' -q; \
    fi && \
    echo "Python shell (venv activated)" && \
    .venv/bin/python3

# Enter Python REPL for quick imports
python:
    @cd backend && \
    if [ ! -d ".venv" ]; then \
        python3.12 -m venv .venv && \
        .venv/bin/python3 -m ensurepip --upgrade > /dev/null 2>&1 || true && \
        .venv/bin/python3 -m pip install --upgrade pip setuptools wheel -q && \
        .venv/bin/python3 -m pip install -e '.[dev]' -q; \
    fi && \
    .venv/bin/python3 -c "from src.app.auth.models import InviteCodeModel; print('✓ Imports work'); import code; code.interact(local=globals())"

# Run Python script with correct environment
run-py script:
    @cd backend && \
    if [ ! -d ".venv" ]; then \
        python3.12 -m venv .venv && \
        .venv/bin/python3 -m ensurepip --upgrade > /dev/null 2>&1 || true && \
        .venv/bin/python3 -m pip install --upgrade pip setuptools wheel -q && \
        .venv/bin/python3 -m pip install -e '.[dev]' -q; \
    fi && \
    .venv/bin/python3 {{script}}

# Clean environments (keep source code, remove generated files)
clean:
    @echo "Cleaning environments..."
    @rm -rf backend/.venv
    @rm -rf node_modules
    @rm -rf dist
    @rm -rf backend/__pycache__
    @rm -rf .pytest_cache
    @echo "✓ Cleaned (run 'just setup' to reinstall)"
```

## Step 4: Update Docker Compose for Caddy Integration

### 4.1 Update Development Docker Compose

**File: `docker-compose.dev.yml`**

```yaml
version: '3.8'

services:
  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    environment:
      - CADDY_INGRESS_NETWORKS=caddy
    networks:
      - caddy
      - app
    restart: unless-stopped

  backend:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/hey_sh_dev
      - REDIS_URL=redis://redis:6379
      - TEMPORAL_ADDRESS=temporal:7233
    depends_on:
      - postgres
      - redis
      - temporal
    networks:
      - app
    restart: unless-stopped
    # No external ports - accessed through Caddy

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    environment:
      - REACT_APP_API_URL=https://dev-api.hey.sh
    networks:
      - app
    restart: unless-stopped
    # No external ports - accessed through Caddy

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=hey_sh_dev
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app
    restart: unless-stopped
    # No external ports - internal service only

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    networks:
      - app
    restart: unless-stopped
    # No external ports - internal service only

  temporal:
    image: temporalio/auto-setup:latest
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=user
      - POSTGRES_PWD=password
      - POSTGRES_SEEDS=postgres
    depends_on:
      - postgres
    networks:
      - app
    restart: unless-stopped
    # No external ports - accessed through Caddy

volumes:
  caddy_data:
  caddy_config:
  postgres_data:
  redis_data:

networks:
  caddy:
    external: true
  app:
    driver: bridge
```

## Step 5: Validation and Testing

### 5.1 Create Validation Script

**File: `scripts/validate-config.py`**

```python
#!/usr/bin/env python3
"""
Configuration validation script.
Validates that all configurations are correct and consistent.
"""

import sys
from pathlib import Path
from config.hostnames import hostname_config
from config.constants import Constants

def validate_configuration():
    """Validate all configuration settings."""
    print("🔍 Validating configuration...")

    errors = []

    # Validate hostname configuration
    try:
        print("  ✓ Hostname configuration loaded")
        print(f"    Environment: {hostname_config.environment}")
        print(f"    App hostname: {hostname_config.app_hostname}")
        print(f"    API hostname: {hostname_config.api_hostname}")
    except Exception as e:
        errors.append(f"Hostname configuration error: {e}")

    # Validate port allocation
    try:
        ports = hostname_config.ports
        dev_ports = hostname_config.dev_ports

        # Check for port conflicts
        all_ports = list(ports.values()) + list(dev_ports.values())
        if len(all_ports) != len(set(all_ports)):
            errors.append("Port conflicts detected")

        print("  ✓ Port allocation validated")
        print(f"    Production ports: {ports}")
        print(f"    Development ports: {dev_ports}")
    except Exception as e:
        errors.append(f"Port allocation error: {e}")

    # Validate constants
    try:
        print("  ✓ Constants loaded")
        print(f"    API base URL: {Constants.API_BASE_URL}")
        print(f"    Health check endpoint: {Constants.HEALTH_CHECK_ENDPOINT}")
    except Exception as e:
        errors.append(f"Constants error: {e}")

    if errors:
        print("\n❌ Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("\n✅ Configuration validation passed")
        return True

if __name__ == "__main__":
    success = validate_configuration()
    sys.exit(0 if success else 1)
```

### 5.2 Create Test Script

**File: `scripts/test-config.py`**

```python
#!/usr/bin/env python3
"""
Test configuration script.
Tests that all configurations work correctly.
"""

import sys
from config.hostnames import hostname_config
from config.constants import Constants

def test_configuration():
    """Test configuration functionality."""
    print("🧪 Testing configuration...")

    try:
        # Test hostname retrieval
        app_hostname = hostname_config.get_hostname("app")
        api_hostname = hostname_config.get_hostname("api")
        print(f"  ✓ App hostname: {app_hostname}")
        print(f"  ✓ API hostname: {api_hostname}")

        # Test port retrieval
        backend_port = hostname_config.get_port("backend")
        frontend_port = hostname_config.get_port("frontend")
        print(f"  ✓ Backend port: {backend_port}")
        print(f"  ✓ Frontend port: {frontend_port}")

        # Test service URL retrieval
        backend_url = hostname_config.get_service_url("backend")
        frontend_url = hostname_config.get_service_url("frontend")
        print(f"  ✓ Backend URL: {backend_url}")
        print(f"  ✓ Frontend URL: {frontend_url}")

        # Test constants
        print(f"  ✓ API base URL: {Constants.API_BASE_URL}")
        print(f"  ✓ Health check endpoint: {Constants.HEALTH_CHECK_ENDPOINT}")

        print("\n✅ Configuration testing passed")
        return True

    except Exception as e:
        print(f"\n❌ Configuration testing failed: {e}")
        return False

if __name__ == "__main__":
    success = test_configuration()
    sys.exit(0 if success else 1)
```

## Step 6: Update Documentation

### 6.1 Create Setup Guide

**File: `docs/SETUP.md`**

```markdown
# Setup Guide

## Prerequisites

- Python 3.12+
- Node.js 18+
- Docker and Docker Compose
- Caddy (for reverse proxy)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hey-sh-workflow
   ```

2. **Set up development environment**
   ```bash
   just setup
   ```

3. **Configure local domains**
   ```bash
   just hosts-setup
   ```

4. **Start all services**
   ```bash
   just dev-full
   ```

## Access Points

- **Frontend**: https://dev.hey.sh
- **API**: https://dev-api.hey.sh
- **Temporal UI**: https://temporal.hey.sh
- **Grafana**: https://grafana.hey.sh
- **Prometheus**: https://prometheus.hey.sh

## Configuration

All configuration is centralized in the `config/` directory:

- `config/hostnames.py` - Hostname and port configuration
- `config/constants.py` - Application constants and text strings
- `config/environments/` - Environment-specific configurations

## Troubleshooting

### Port Conflicts
If you encounter port conflicts, check the port allocation in `config/hostnames.py` and ensure no other services are using the same ports.

### Domain Resolution
If domains don't resolve, ensure you've run `just hosts-setup` and that the entries are correctly added to `/etc/hosts`.

### Service Health
Check service health with:
```bash
just health-check
```

## Development Workflow

1. **Start services**: `just docker-up`
2. **Start frontend**: `just dev` (in separate terminal)
3. **Start backend**: `just dev-api` (in separate terminal)
4. **Check health**: `just health-check`
5. **View logs**: `just docker-logs`

## Cleanup

To clean up the development environment:
```bash
just clean
just hosts-cleanup
```
```

## Implementation Checklist

### Phase 1: Configuration Centralization
- [ ] Create `config/` directory structure
- [ ] Implement `config/hostnames.py` with centralized configuration
- [ ] Create `config/constants.py` with all text strings
- [ ] Implement environment-specific configurations
- [ ] Update Caddyfile with real hostnames
- [ ] Update Justfile to use centralized configuration
- [ ] Update Docker Compose for Caddy integration
- [ ] Create validation and test scripts
- [ ] Update documentation

### Testing
- [ ] Run configuration validation: `python scripts/validate-config.py`
- [ ] Run configuration testing: `python scripts/test-config.py`
- [ ] Test hostname resolution
- [ ] Test port allocation
- [ ] Test service URLs
- [ ] Test Caddy configuration
- [ ] Test Docker Compose setup

### Validation
- [ ] All hostnames use `.hey.sh` domain
- [ ] No localhost references in configuration
- [ ] All ports are unique and within valid range
- [ ] Environment-specific configurations work
- [ ] Caddy configuration is valid
- [ ] Docker Compose starts all services
- [ ] All services are accessible through Caddy

This implementation guide provides a comprehensive approach to implementing Phase 1 of the codebase standards plan, ensuring that all configuration is centralized and uses real hostnames instead of localhost and port numbers.

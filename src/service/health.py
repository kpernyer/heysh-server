"""Health check and readiness probe endpoints for pods.
Provides comprehensive system status information for Kubernetes probes.
"""

import asyncio
import os
from datetime import datetime
from typing import Any

import structlog

logger = structlog.get_logger()


class HealthStatus:
    """Health status object."""

    def __init__(
        self, status: str, message: str = "", details: dict[str, Any] | None = None
    ):
        self.status = status  # "healthy", "degraded", "unhealthy"
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status,
            "message": self.message,
            "timestamp": self.timestamp,
            "details": self.details,
        }


async def check_temporal_connection(client: Any) -> HealthStatus:
    """Check Temporal server connection."""
    try:
        if not client:
            return HealthStatus("unhealthy", "Temporal client not initialized")

        # Simple health check via Temporal
        await asyncio.wait_for(
            client.get_worker_task_reachability(),
            timeout=5.0,
        )
        return HealthStatus("healthy", "Connected to Temporal")
    except TimeoutError:
        return HealthStatus("degraded", "Temporal connection timeout")
    except Exception as e:
        return HealthStatus("unhealthy", f"Temporal connection failed: {e!s}")


async def check_database_connections() -> HealthStatus:
    """Check database connections using hostname-based configuration."""
    from src.service.config import get_settings

    settings = get_settings()
    issues = []

    # Check Neo4j
    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        with driver.session() as session:
            session.run("RETURN 1")
        driver.close()
    except Exception as e:
        issues.append(f"Neo4j: {e!s}")

    # Check Weaviate
    try:
        import weaviate

        client = weaviate.Client(settings.weaviate_url)
        client.schema.get()
    except Exception as e:
        issues.append(f"Weaviate: {e!s}")

    # Check PostgreSQL (via asyncpg)
    try:
        import asyncpg

        conn = await asyncpg.connect(
            host=os.getenv("DATABASE_HOST", "localhost"),
            port=int(os.getenv("DATABASE_PORT", "5432")),
            user=os.getenv("DATABASE_USER", "postgres"),
            password=os.getenv("DATABASE_PASSWORD", ""),
            database=os.getenv("DATABASE_NAME", "hey_sh"),
        )
        await conn.execute("SELECT 1")
        await conn.close()
    except Exception as e:
        issues.append(f"PostgreSQL: {e!s}")

    if not issues:
        return HealthStatus("healthy", "All databases connected")
    elif len(issues) < 3:
        return HealthStatus(
            "degraded",
            f"{len(issues)} database(s) unreachable",
            {"issues": issues},
        )
    else:
        return HealthStatus(
            "unhealthy",
            "All databases unreachable",
            {"issues": issues},
        )


async def check_external_services() -> HealthStatus:
    """Check external service connectivity."""
    issues = []

    # Check OpenAI API key availability
    if not os.getenv("OPENAI_API_KEY"):
        issues.append("OpenAI API key not configured")

    # Check Supabase availability
    if not os.getenv("SUPABASE_URL"):
        issues.append("Supabase not configured")

    # Check required environment variables
    required_vars = [
        "TEMPORAL_ADDRESS",
        "TEMPORAL_NAMESPACE",
    ]
    for var in required_vars:
        if not os.getenv(var):
            issues.append(f"Missing {var}")

    if not issues:
        return HealthStatus("healthy", "All external services configured")
    else:
        return HealthStatus(
            "degraded",
            f"{len(issues)} configuration issue(s)",
            {"issues": issues},
        )


async def get_system_info() -> dict[str, Any]:
    """Get system information."""
    import platform

    return {
        "hostname": os.getenv("HOSTNAME", "unknown"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "pod_name": os.getenv("POD_NAME", "unknown"),
        "pod_namespace": os.getenv("POD_NAMESPACE", "default"),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }


async def run_readiness_check(temporal_client: Any) -> dict[str, Any]:
    """Readiness check - service can handle traffic.
    Called frequently by Kubernetes readiness probes.
    """
    temporal_status = await check_temporal_connection(temporal_client)
    db_status = await check_database_connections()
    services_status = await check_external_services()

    # Ready if all critical services are healthy or degraded
    is_ready = temporal_status.status in (
        "healthy",
        "degraded",
    ) and db_status.status in (
        "healthy",
        "degraded",
    )

    return {
        "ready": is_ready,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": {
            "temporal": temporal_status.to_dict(),
            "databases": db_status.to_dict(),
            "services": services_status.to_dict(),
        },
    }


async def run_liveness_check(temporal_client: Any) -> dict[str, Any]:
    """Liveness check - service should be restarted if fails.
    Called periodically by Kubernetes liveness probes.
    """
    temporal_status = await check_temporal_connection(temporal_client)

    # Only restart if Temporal is completely down
    is_alive = temporal_status.status != "unhealthy"

    return {
        "alive": is_alive,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": {
            "temporal": temporal_status.to_dict(),
        },
    }


async def run_startup_check(temporal_client: Any) -> dict[str, Any]:
    """Startup check - service completed initialization.
    Called once on pod startup before readiness checks.
    """
    temporal_status = await check_temporal_connection(temporal_client)
    services_status = await check_external_services()

    # Startup complete if Temporal and services are configured
    is_started = (
        temporal_status.status != "unhealthy" and services_status.status != "unhealthy"
    )

    system_info = await get_system_info()

    return {
        "started": is_started,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "system": system_info,
        "checks": {
            "temporal": temporal_status.to_dict(),
            "services": services_status.to_dict(),
        },
    }

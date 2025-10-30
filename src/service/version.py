"""Backend version and build information."""

import os
from pathlib import Path

# Read version from pyproject.toml
PYPROJECT_PATH = Path(__file__).parent.parent.parent / "pyproject.toml"
VERSION = "1.0.7"  # Default version

if PYPROJECT_PATH.exists():
    try:
        with open(PYPROJECT_PATH) as f:
            for line in f:
                if line.startswith('version = "'):
                    VERSION = line.split('"')[1]
                    break
    except Exception:
        pass


def get_api_version() -> str:
    """Get the API version for FastAPI documentation."""
    return VERSION


def get_backend_info() -> dict[str, str | None]:
    """Get backend information including version, git SHA, and build metadata.

    Build metadata is injected at Docker build time via environment variables:
    - GIT_SHA: Short git commit hash (e.g., "4dc7afc")
    - BUILD_TIME: ISO timestamp when image was built
    - ENVIRONMENT: production/development/staging
    """
    return {
        "version": VERSION,
        "git_sha": os.getenv("GIT_SHA"),
        "built_at": os.getenv("BUILD_TIME"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "api_version": "v2",  # Now using API v2
    }

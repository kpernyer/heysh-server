"""Backend version and build information."""

import os
import subprocess
from datetime import datetime
from pathlib import Path

# Read version from pyproject.toml
PYPROJECT_PATH = Path(__file__).parent.parent / "pyproject.toml"
VERSION = "0.1.0"

if PYPROJECT_PATH.exists():
    try:
        with open(PYPROJECT_PATH) as f:
            for line in f:
                if line.startswith('version = "'):
                    VERSION = line.split('"')[1]
                    break
    except Exception:
        pass


def get_git_commit() -> str | None:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_git_commit_date() -> str | None:
    """Get current git commit date/time."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%aI"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_backend_info() -> dict[str, str | None]:
    """Get backend information including version, commit, and timestamp."""
    return {
        "version": VERSION,
        "commit": get_git_commit(),
        "commit_date": get_git_commit_date(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

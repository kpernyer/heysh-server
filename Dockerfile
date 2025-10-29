# Hey.sh Server - Python Backend Dockerfile
# Multi-stage build for optimal layer caching

# Stage 1: Dependencies (cached separately)
FROM python:3.11-slim AS dependencies

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies (rarely changes)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (rarely changes)
RUN pip install uv

WORKDIR /app

# Copy only dependency files (changes less often than code)
COPY requirements.txt pyproject.toml ./

# Install Python dependencies (this layer gets cached)
RUN uv pip install --system -r requirements.txt

# Stage 2: Application
FROM dependencies AS base

# Build arguments for version tracking
ARG GIT_SHA
ARG BUILD_TIME
ARG ENVIRONMENT=production

# Set build metadata as environment variables
ENV GIT_SHA=${GIT_SHA}
ENV BUILD_TIME=${BUILD_TIME}
ENV ENVIRONMENT=${ENVIRONMENT}

# Copy application code (changes frequently, but built on cached deps)
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uv", "run", "uvicorn", "src.service.api:app", "--host", "0.0.0.0", "--port", "8000"]
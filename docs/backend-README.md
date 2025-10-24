# Hey.sh Backend

Backend orchestration layer for the hey.sh knowledge platform.

## Architecture

This backend follows Kenneth Pernyer's singular directory conventions with:

- **Temporal workflows** for orchestration
- **Neo4j** for knowledge graphs
- **Weaviate** for vector search
- **FastAPI** for REST API
- **Prompts-as-code** system

### Directory Structure

```
backend/
├── workflow/         # Temporal workflow definitions
├── activity/         # Temporal activities
├── worker/          # Temporal workers
├── service/         # FastAPI services
├── src/            # Shared application code
│   └── app/
│       ├── clients/   # Database/API clients
│       ├── models/    # Data models
│       ├── schemas/   # Pydantic schemas
│       └── utils/     # Utilities
├── prompt/          # Prompts-as-code
│   ├── coding/       # *.prompt.md (code generation)
│   └── api-calling/  # *.prompt.yaml (LLM API calls)
├── tool/            # Development tools
├── script/          # Executable scripts
├── test/            # Tests
├── infra/           # Infrastructure as code
└── docker/          # Docker configurations
```

### Import Rules

- `workflow`, `activity`, `worker`, `service` **MAY** import from `src/app/**`
- `src/app/**` **MUST NOT** import from `workflow`, `activity`, `worker`, `service`

This ensures core application logic remains independent of orchestration.

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- [uv](https://github.com/astral-sh/uv) (fast Python package manager)
- [just](https://github.com/casey/just) (command runner)

### Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install just (if not already installed)
# macOS
brew install just
# Linux
cargo install just

# Bootstrap the project
just bootstrap

# Start development environment
just dev
```

This will start:
- Temporal server + UI (http://localhost:8080)
- Neo4j (http://localhost:7474)
- Weaviate (http://localhost:8081)
- PostgreSQL
- FastAPI backend (http://localhost:8000)

## Common Commands

```bash
just dev              # Start all services
just dev-stop         # Stop all services
just test             # Run tests
just test-cov         # Run tests with coverage
just lint             # Lint code
just fmt              # Format code
just check-structure  # Validate repo structure
just worker           # Run Temporal worker
just clean            # Clean build artifacts
```

## Development

### Running Tests

```bash
# All tests
just test

# Specific test file
just test-file test/workflow/test_document_processing.py

# With coverage report
just test-cov
```

### Linting and Formatting

```bash
# Check code quality
just lint

# Auto-format code
just fmt
```

### Prompts-as-Code

Render API-calling prompts with variable substitution:

```bash
just render-prompt prompt/api-calling/summarize-document.v1.prompt.yaml \
  '{"title":"Test Doc","domain":"AI","content":"..."}'
```

## Deployment

### Docker

```bash
# Build image
just docker-build

# Run locally
docker run -p 8000:8000 hey-sh-backend:latest
```

### Google Cloud Platform

```bash
# Deploy (requires gcloud auth)
just deploy
```

This will:
1. Apply Terraform infrastructure
2. Build and push Docker image to GCR
3. Deploy to Cloud Run

## Documentation

- [Basics](docs/basics.md) - Getting started guide
- [Extensions Index](docs/EXTENSIONS_INDEX.md) - All extension guides

## Tech Stack

- **[Temporal](https://temporal.io)** - Workflow orchestration
- **[FastAPI](https://fastapi.tiangolo.com)** - Web framework
- **[Neo4j](https://neo4j.com)** - Graph database
- **[Weaviate](https://weaviate.io)** - Vector database
- **[uv](https://github.com/astral-sh/uv)** - Package manager
- **[ruff](https://github.com/astral-sh/ruff)** - Linter
- **[black](https://github.com/psf/black)** - Formatter
- **[mypy](https://github.com/python/mypy)** - Type checker
- **[pytest](https://pytest.org)** - Testing framework

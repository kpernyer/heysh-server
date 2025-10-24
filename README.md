# Hey.sh Server

Python backend server for the Hey.sh knowledge management platform.

## 🏗️ Architecture

- **Temporal Workflows**: Document processing, domain bootstrapping, human-in-the-loop
- **FastAPI**: REST API server
- **Supabase**: Database and storage
- **Weaviate**: Vector database for semantic search
- **Neo4j**: Knowledge graph
- **OpenRouter**: LLM routing and cost optimization

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- `uv` package manager
- Temporal server
- Supabase project
- Weaviate instance
- Neo4j instance

### Installation

```bash
# Install dependencies
uv pip install -r requirements.txt

# Start Temporal server
just start-temporal

# Start workers
just start-workers

# Start API server
just start-api
```

### Development

```bash
# Run tests
just test

# Run linting
just lint

# Run type checking
just type-check
```

## 📁 Project Structure

```
heysh-server/
├── src/                    # Core business logic
│   ├── app/               # Application layer
│   │   ├── models/        # Pydantic models
│   │   ├── schemas/       # API schemas
│   │   └── services/      # Business services
│   └── config/            # Configuration
├── workflow/              # Temporal workflows
├── activity/              # Temporal activities
├── worker/                # Temporal workers
├── service/               # FastAPI routes
├── test/                  # Tests
├── scripts/               # Utility scripts
├── examples/              # Example domains
└── docs/                  # Documentation
```

## 🔧 Configuration

All configuration is centralized in `config/` directory:

- `hostnames.py`: Hostname and port management
- `constants.py`: Text strings and constants
- `environments/`: Environment-specific configs

## 🧪 Testing

```bash
# Run all tests
just test

# Run specific test
just test-workflow

# Run with coverage
just test-coverage
```

## 📚 Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Development Guide](docs/DEVELOPMENT.md)

## 🚀 Deployment

```bash
# Build Docker image
just build

# Deploy to staging
just deploy-staging

# Deploy to production
just deploy-prod
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

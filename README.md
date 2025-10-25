# Hey.sh Server

Python backend server for the Hey.sh knowledge management platform with Temporal workflows, FastAPI, and comprehensive local development setup.

## 🏗️ Architecture

- **Temporal Workflows**: Document processing, domain bootstrapping, human-in-the-loop
- **FastAPI**: REST API server with WebSocket support
- **Supabase**: Database and storage (local MinIO alternative)
- **Weaviate**: Vector database for semantic search
- **Neo4j**: Knowledge graph
- **OpenRouter**: LLM routing and cost optimization
- **Caddy**: Reverse proxy with automatic HTTPS

## 🚀 Quick Start

### **Prerequisites**
```bash
# Install all external dependencies
just bootstrap
```

### **HTTPS Development (Recommended)**
```bash
# Generate SSL certificates
just setup-ssl

# Start HTTPS development environment
just dev-https
```

### **HTTP Development**
```bash
# Start HTTP development environment
just dev
```

## 🌐 Access Your Application

### **HTTPS Development**
- **Frontend**: `https://www.hey.local`
- **API**: `https://api.hey.local`
- **Temporal UI**: `https://temporal.hey.local`
- **Neo4j Browser**: `https://neo4j.hey.local`
- **Weaviate**: `https://weaviate.hey.local`

### **HTTP Development**
- **Frontend**: `http://hey.local`
- **API**: `http://api.hey.local`
- **Temporal UI**: `http://temporal.hey.local`
- **Neo4j Browser**: `http://neo4j.hey.local`
- **Weaviate**: `http://weaviate.hey.local`

## 📁 Project Structure

```
heysh-server/
├── src/                    # All Python code
│   ├── app/               # Core business logic
│   │   ├── models/        # Pydantic models
│   │   ├── schemas/       # API schemas
│   │   ├── services/      # Business services
│   │   ├── clients/       # External API clients
│   │   └── utils/         # Utilities
│   ├── workflow/          # Temporal workflows
│   ├── activity/          # Temporal activities
│   ├── worker/            # Temporal workers
│   ├── service/           # FastAPI routes
│   └── config/            # Configuration
├── test/                  # Tests
├── script/                # Utility scripts
├── example/               # Example domains
├── doc/                   # Documentation
├── infra/                 # Infrastructure (Terraform, K8s)
├── deployments/           # Deployment configs
├── docker/                # Docker configs
└── monitoring/            # Monitoring configs
```

## 🔧 Development Commands

### **Setup**
```bash
just bootstrap          # Install all external dependencies
just install            # Install Python dependencies
just build              # Build the project
just setup-ssl          # Generate SSL certificates
```

### **Development**
```bash
just dev                # Start HTTP development environment
just dev-https          # Start HTTPS development environment
just up-infra           # Start infrastructure services only
just verify             # Check if all services are running
just clean              # Stop and clean up all services
just reboot             # Clean restart everything
```

### **Development Tools**
```bash
just workers            # Start Temporal workers
just caddy-https         # Start Caddy with HTTPS
just caddy-prod         # Start Caddy for production hostnames
just monitoring         # Start monitoring services
```

### **Testing**
```bash
just test               # Run tests
just test-api           # Run API endpoint tests
just test-users         # Run user endpoint tests
just test-membership    # Run membership endpoint tests
just test-all           # Run comprehensive test suite
```

### **Code Quality**
```bash
just format             # Format code
just lint               # Lint code
just type-check         # Type check code
```

## 🔐 HTTPS Development Benefits

1. **Production-like**: Matches your production HTTPS environment
2. **No SSL Errors**: Proper certificates eliminate browser warnings
3. **WebSocket Support**: `wss://` works properly with HTTPS
4. **CORS Resolution**: HTTPS CORS configuration matches production
5. **Security Testing**: Test HTTPS-specific features locally

## 📚 Documentation

- [HTTPS Development Setup](doc/HTTPS_DEVELOPMENT_SETUP.md) - Complete HTTPS setup guide
- [Local Development Setup](doc/LOCAL_DEVELOPMENT_SETUP.md) - Port and hostname mapping
- [Production Deployment](doc/PRODUCTION_DEPLOYMENT.md) - Production deployment guide
- [API Documentation](doc/API.md) - API endpoints and usage
- [Architecture Guide](doc/ARCHITECTURE.md) - System architecture overview

## 🚀 Deployment

### **Local Development**
```bash
# Start development environment
just dev-https
```

### **Production Deployment**
```bash
# Start production services
just up-infra

# Start production Caddy
just caddy-prod

# Start monitoring (optional)
just monitoring
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.
# Hey.sh Development Guide

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

## 🌐 Service URLs

### **HTTPS Development**
- **Frontend**: `https://www.hey.local`
- **API**: `https://api.hey.local`
- **Temporal UI**: `https://temporal.hey.local`
- **Neo4j Browser**: `https://neo4j.hey.local`
- **Weaviate**: `https://weaviate.hey.local`
- **Database**: `https://db.hey.local`
- **Redis**: `https://redis.hey.local`
- **MinIO**: `https://supabase.hey.local`

### **HTTP Development**
- **Frontend**: `http://hey.local`
- **API**: `http://api.hey.local`
- **Temporal UI**: `http://temporal.hey.local`
- **Neo4j Browser**: `http://neo4j.hey.local`
- **Weaviate**: `http://weaviate.hey.local`
- **Database**: `http://db.hey.local`
- **Redis**: `http://redis.hey.local`
- **MinIO**: `http://supabase.hey.local`

## 🔧 Development Commands

### **Setup Commands**
```bash
just bootstrap          # Install all external dependencies
just install            # Install Python dependencies
just build              # Build the project
just setup-ssl          # Generate SSL certificates
```

### **Development Commands**
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

### **Testing Commands**
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

## 🔐 HTTPS Development Setup

### **Why HTTPS?**
1. **Production-like**: Matches your production HTTPS environment
2. **No SSL Errors**: Proper certificates eliminate browser warnings
3. **WebSocket Support**: `wss://` works properly with HTTPS
4. **CORS Resolution**: HTTPS CORS configuration matches production
5. **Security Testing**: Test HTTPS-specific features locally

### **Setup Steps**
1. **Install Dependencies**: `just bootstrap`
2. **Generate Certificates**: `just setup-ssl`
3. **Start HTTPS Dev**: `just dev-https`

### **Manual Setup**
```bash
# Install mkcert
brew install mkcert

# Install CA certificate
sudo mkcert -install

# Generate certificates
mkcert hey.local www.hey.local api.hey.local temporal.hey.local neo4j.hey.local weaviate.hey.local db.hey.local redis.hey.local minio.hey.local supabase.hey.local monitoring.hey.local grafana.hey.local alertmanager.hey.local jaeger.hey.local loki.hey.local
```

## 🌐 Hostname Configuration

### **Local Development (/etc/hosts)**
```bash
# Core Application Services
127.0.0.1 hey.local
127.0.0.1 www.hey.local
127.0.0.1 api.hey.local
127.0.0.1 temporal.hey.local

# Database & Storage Services
127.0.0.1 db.hey.local
127.0.0.1 neo4j.hey.local
127.0.0.1 weaviate.hey.local
127.0.0.1 redis.hey.local
127.0.0.1 supabase.hey.local

# Monitoring Services (Optional)
127.0.0.1 monitoring.hey.local
127.0.0.1 grafana.hey.local
127.0.0.1 alertmanager.hey.local
127.0.0.1 jaeger.hey.local
127.0.0.1 loki.hey.local
```

### **Production DNS Configuration**
```bash
# Core Application Services
hey.sh                    A    <your-server-ip>
www.hey.sh               A    <your-server-ip>
api.hey.sh               A    <your-server-ip>
temporal.hey.sh          A    <your-server-ip>

# Database & Storage Services
db.hey.sh                A    <your-server-ip>
neo4j.hey.sh             A    <your-server-ip>
weaviate.hey.sh          A    <your-server-ip>
redis.hey.sh             A    <your-server-ip>
supabase.hey.sh          A    <your-server-ip>

# Monitoring Services (Optional)
monitoring.hey.sh        A    <your-server-ip>
grafana.hey.sh           A    <your-server-ip>
alertmanager.hey.sh       A    <your-server-ip>
jaeger.hey.sh            A    <your-server-ip>
loki.hey.sh              A    <your-server-ip>
```

## 🔧 Configuration Management

### **Environment Variables**
```bash
# Development
HEY_ENV=development
HEY_HTTPS=true

# Production
HEY_ENV=production
```

### **Configuration Usage**
```python
from src.config import config, API_URL, FRONTEND_URL

# Get URLs for current environment
api_url = config.get_url("api")        # https://api.hey.local or https://api.hey.sh
frontend_url = config.get_url("frontend")  # https://www.hey.local or https://www.hey.sh
```

## 🧪 Testing

### **Running Tests**
```bash
# Run all tests
just test

# Run specific test suites
just test-api
just test-users
just test-membership

# Run with coverage
just test-coverage
```

### **Test Structure**
```
test/
├── test_api_endpoints.py      # API endpoint tests
├── test_user_endpoints.py     # User endpoint tests
├── test_membership_endpoints.py # Membership endpoint tests
├── test_connectivity.py       # Service connectivity tests
└── run_tests.py              # Test runner
```

## 🐛 Troubleshooting

### **Port Conflicts**
```bash
# Kill processes on common ports
lsof -ti:8002,443,80 | xargs kill -9 2>/dev/null || echo "No processes found"
```

### **Docker Issues**
```bash
# Restart Docker Desktop
# Or restart Docker daemon
sudo launchctl stop com.docker.docker
sudo launchctl start com.docker.docker
```

### **SSL Certificate Issues**
```bash
# Reinstall CA certificate
sudo mkcert -uninstall
sudo mkcert -install

# Regenerate certificates
rm hey.local+*.pem
mkcert hey.local www.hey.local api.hey.local temporal.hey.local neo4j.hey.local weaviate.hey.local db.hey.local redis.hey.local minio.hey.local supabase.hey.local monitoring.hey.local grafana.hey.local alertmanager.hey.local jaeger.hey.local loki.hey.local
```

### **Caddy Issues**
```bash
# Check Caddy configuration
caddy validate --config docker/Caddyfile.https

# Format Caddyfile
caddy fmt --overwrite docker/Caddyfile.https
```

## 📊 Monitoring

### **Start Monitoring**
```bash
just monitoring
```

### **Access Monitoring Services**
- **Prometheus**: `https://monitoring.hey.local`
- **Grafana**: `https://grafana.hey.local`
- **Alertmanager**: `https://alertmanager.hey.local`
- **Jaeger**: `https://jaeger.hey.local`
- **Loki**: `https://loki.hey.local`

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

## 🔄 Workflow Development

### **Adding New Workflows**
1. Create workflow in `src/workflow/`
2. Create activities in `src/activity/`
3. Register in `src/worker/`
4. Add API endpoints in `src/service/`

### **Testing Workflows**
```bash
# Start workers
just workers

# Test workflow execution
curl -X POST https://api.hey.local/api/v1/documents \
  -H "Authorization: Bearer <token>" \
  -F "file=@test.pdf" \
  -F "domain_id=uuid"
```

## 📝 Best Practices

### **Code Organization**
- **Clean Architecture**: Dependency inversion
- **Domain-Driven Design**: Business logic separation
- **Test-Driven Development**: Comprehensive test coverage
- **Code Quality**: Linting, formatting, type checking

### **Development Workflow**
1. **Start Environment**: `just dev-https`
2. **Make Changes**: Edit code with hot reload
3. **Run Tests**: `just test`
4. **Check Quality**: `just lint && just type-check`
5. **Commit Changes**: Git workflow

### **Configuration Management**
- **Environment Variables**: Use for configuration
- **Centralized Config**: Single source of truth
- **Hostname Management**: Dynamic URL generation
- **Protocol Detection**: HTTP vs HTTPS

---

This development guide provides everything you need to work with the Hey.sh platform locally and deploy to production.
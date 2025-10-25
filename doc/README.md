# Hey.sh Documentation

## 📚 Documentation Overview

This directory contains the essential documentation for the Hey.sh knowledge management platform.

## 📖 Core Documentation

### **Essential Guides**
- **[README.md](../README.md)** - Main project README with quick start
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Complete development guide
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture overview
- **[API.md](API.md)** - API documentation and endpoints
- **[HTTPS_DEVELOPMENT_SETUP.md](HTTPS_DEVELOPMENT_SETUP.md)** - HTTPS development setup

## 🔧 Specialized Documentation

### **Integration Guides**
- **[AUTH_INTEGRATION_GUIDE.md](AUTH_INTEGRATION_GUIDE.md)** - Authentication integration
- **[TEMPORAL_INTEGRATION.md](TEMPORAL_INTEGRATION.md)** - Temporal workflow integration
- **[FRONTEND_BACKEND_INTEGRATION.md](FRONTEND_BACKEND_INTEGRATION.md)** - Frontend-backend integration
- **[WEBSOCKET_INTEGRATION.md](WEBSOCKET_INTEGRATION.md)** - WebSocket integration

### **Infrastructure & Operations**
- **[INFRASTRUCTURE.md](INFRASTRUCTURE.md)** - Infrastructure setup
- **[KUBERNETES_HEALTH_CHECKS.md](KUBERNETES_HEALTH_CHECKS.md)** - Kubernetes health checks
- **[WORKERS.md](WORKERS.md)** - Temporal workers documentation

### **Development Tools**
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Testing strategies and examples

### **AI Assistant Prompts**
- **[add-activity.prompt.md](add-activity.prompt.md)** - Template for creating Temporal activities
- **[add-workflow.prompt.md](add-workflow.prompt.md)** - Template for creating Temporal workflows

## 🚀 Quick Start

### **For Developers**
1. **Start Here**: [README.md](../README.md) - Project overview and quick start
2. **Development**: [DEVELOPMENT.md](DEVELOPMENT.md) - Complete development setup
3. **HTTPS Setup**: [HTTPS_DEVELOPMENT_SETUP.md](HTTPS_DEVELOPMENT_SETUP.md) - HTTPS development

### **For DevOps**
1. **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md) - System design
2. **Deployment**: [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment
3. **Infrastructure**: [INFRASTRUCTURE.md](INFRASTRUCTURE.md) - Infrastructure setup

## 🔧 Development Workflow

### **Local Development**
```bash
# Install dependencies
just bootstrap

# Start HTTPS development
just setup-ssl
just dev-https
```

### **Access Services**
- **Frontend**: `https://www.hey.local`
- **API**: `https://api.hey.local`
- **Temporal UI**: `https://temporal.hey.local`
- **Neo4j Browser**: `https://neo4j.hey.local`
- **Weaviate**: `https://weaviate.hey.local`

## 📋 Documentation Structure

### **Core Documentation (6 files)**
- **README.md** - Project overview and quick start
- **DEVELOPMENT.md** - Development setup and workflow
- **DEPLOYMENT.md** - Production deployment guide
- **ARCHITECTURE.md** - System architecture and design
- **API.md** - API documentation and endpoints
- **HTTPS_DEVELOPMENT_SETUP.md** - HTTPS development setup

### **Specialized Documentation (10 files)**
- **Integration Guides** (4 files) - Authentication, Temporal, Frontend-Backend, WebSocket
- **Infrastructure** (3 files) - Infrastructure, Kubernetes, Workers
- **Development Tools** (1 file) - Testing
- **AI Prompts** (2 files) - Activity and workflow templates

## 🎯 Key Features

### **Development**
- **HTTPS Local Development**: Production-like HTTPS environment
- **Hot Reload**: FastAPI development server with hot reload
- **Comprehensive Testing**: API, integration, and connectivity tests
- **Code Quality**: Linting, formatting, and type checking

### **Architecture**
- **Temporal Workflows**: Long-running, fault-tolerant processes
- **FastAPI**: Modern Python web framework
- **Microservices**: Containerized services with Docker
- **Monitoring**: Prometheus, Grafana, Alertmanager, Jaeger, Loki

### **Deployment**
- **Docker**: Containerized deployment
- **Kubernetes**: GKE Autopilot deployment
- **Caddy**: Automatic HTTPS with Let's Encrypt
- **Monitoring**: Comprehensive observability stack

## 🔧 Configuration

### **Environment Variables**
```bash
# Development
HEY_ENV=development
HEY_HTTPS=true

# Production
HEY_ENV=production
```

### **Hostname Configuration**
- **Development**: `.hey.local` domains
- **Production**: `.hey.sh` domains
- **Automatic SSL**: Caddy handles SSL certificates

## 📊 Monitoring

### **Services**
- **Prometheus**: Metrics collection
- **Grafana**: Dashboards and visualization
- **Alertmanager**: Alert routing
- **Jaeger**: Distributed tracing
- **Loki**: Log aggregation

### **Access URLs**
- **Prometheus**: `https://monitoring.hey.local`
- **Grafana**: `https://grafana.hey.local`
- **Alertmanager**: `https://alertmanager.hey.local`
- **Jaeger**: `https://jaeger.hey.local`
- **Loki**: `https://loki.hey.local`

## 🚀 Getting Started

1. **Read the README**: Start with [README.md](../README.md)
2. **Set up Development**: Follow [DEVELOPMENT.md](DEVELOPMENT.md)
3. **Configure HTTPS**: Use [HTTPS_DEVELOPMENT_SETUP.md](HTTPS_DEVELOPMENT_SETUP.md)
4. **Deploy to Production**: Follow [DEPLOYMENT.md](DEPLOYMENT.md)

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Run tests and linting**
5. **Submit a pull request**

## 📄 License

MIT License - see LICENSE file for details.

---

This documentation provides everything you need to develop, deploy, and maintain the Hey.sh knowledge management platform.
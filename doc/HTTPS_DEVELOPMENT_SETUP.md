# 🔐 HTTPS Local Development Setup

This guide walks you through setting up HTTPS local development for Hey.sh, matching your production environment exactly.

## 🚀 Quick Start

### **One-Command Setup**
```bash
# Install all external dependencies
just bootstrap

# Generate SSL certificates
just setup-ssl

# Start HTTPS development environment
just dev-https
```

### **Manual Setup (if needed)**

#### **Step 1: Install External Dependencies**
```bash
# Run the bootstrap script
just bootstrap

# Or install manually:
brew install docker mkcert just uv curl netcat jq
```

#### **Step 2: Generate SSL Certificates**
```bash
# Install CA certificate (one-time)
sudo mkcert -install

# Generate certificates for all hey.local domains
mkcert hey.local www.hey.local api.hey.local temporal.hey.local neo4j.hey.local weaviate.hey.local db.hey.local redis.hey.local minio.hey.local supabase.hey.local monitoring.hey.local grafana.hey.local alertmanager.hey.local jaeger.hey.local loki.hey.local
```

#### **Step 3: Start HTTPS Development**
```bash
# Terminal 1: Start infrastructure
just up-infra

# Terminal 2: Start Caddy with HTTPS
just caddy-https

# Terminal 3: Start API with HTTPS config
HEY_HTTPS=true uv run uvicorn src.service.api:app --reload --host 0.0.0.0 --port 8002

# Terminal 4: Start frontend (in hey-sh-workflow repo)
cd /Users/kpernyer/repo/hey-sh-workflow
npm run dev
```

## 🌐 Access Your Application

Once everything is running, access your application at:

- **Frontend**: `https://www.hey.local`
- **API**: `https://api.hey.local`
- **Temporal UI**: `https://temporal.hey.local`
- **Neo4j Browser**: `https://neo4j.hey.local`
- **Weaviate**: `https://weaviate.hey.local`
- **Database**: `https://db.hey.local`
- **Redis**: `https://redis.hey.local`
- **MinIO**: `https://supabase.hey.local`

## 🔧 Available Commands

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
just caddy-https        # Start Caddy with HTTPS
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

## 📋 External Dependencies

The bootstrap script installs:

- **Docker Desktop**: Container runtime
- **mkcert**: SSL certificate generation
- **just**: Command runner
- **uv**: Python package manager
- **curl**: HTTP client
- **netcat**: Port checking
- **jq**: JSON processing

## 🔐 SSL Certificate Details

- **CA Certificate**: Installed system-wide for trusted local certificates
- **Domain Certificates**: Generated for all hey.local subdomains
- **Certificate Files**: `hey.local+13.pem` and `hey.local+13-key.pem`
- **Auto-renewal**: Handled by mkcert

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

## 🎯 Benefits of HTTPS Development

1. **Production-like**: Matches your production HTTPS environment
2. **No SSL Errors**: Proper certificates eliminate browser warnings
3. **WebSocket Support**: `wss://` works properly with HTTPS
4. **CORS Resolution**: HTTPS CORS configuration matches production
5. **Security Testing**: Test HTTPS-specific features locally

## 📝 Next Steps

1. **Update Frontend Environment**: Set your frontend's `.env.local` to use HTTPS URLs
2. **Test All Endpoints**: Verify all API endpoints work with HTTPS
3. **WebSocket Testing**: Test WebSocket connections over HTTPS
4. **Production Deployment**: Use the same HTTPS configuration for production

## 🆘 Getting Help

If you encounter issues:

1. **Check Service Status**: `just verify`
2. **View Logs**: `just logs`
3. **Clean Restart**: `just clean && just dev-https`
4. **Check Dependencies**: `just bootstrap`

---

**🎉 Your HTTPS development environment is now ready!**

# Hey.sh Deployment Guide

## 🚀 Production Deployment

### **Prerequisites**
- Docker and Docker Compose
- Domain name configured
- SSL certificates (Caddy handles this automatically)
- Environment variables configured

### **Quick Deployment**
```bash
# Start production services
just up-infra

# Start production Caddy
just caddy-prod

# Start monitoring (optional)
just monitoring
```

## 🌐 Production Hostname Mapping

### **Core Application Services**
- **Frontend**: `https://www.hey.sh`
- **API**: `https://api.hey.sh`
- **Temporal UI**: `https://temporal.hey.sh`

### **Database & Storage Services**
- **PostgreSQL**: `https://db.hey.sh`
- **Neo4j**: `https://neo4j.hey.sh`
- **Weaviate**: `https://weaviate.hey.sh`
- **Redis**: `https://redis.hey.sh`
- **MinIO**: `https://supabase.hey.sh`

### **Monitoring Services**
- **Prometheus**: `https://monitoring.hey.sh`
- **Grafana**: `https://grafana.hey.sh`
- **Alertmanager**: `https://alertmanager.hey.sh`
- **Jaeger**: `https://jaeger.hey.sh`
- **Loki**: `https://loki.hey.sh`

## 🔧 DNS Configuration

### **Required DNS Records**
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

## 🔐 SSL/TLS Configuration

### **Automatic SSL with Caddy**
Caddy automatically handles SSL certificates using Let's Encrypt:

```bash
# Start Caddy for production
just caddy-prod
```

### **Manual SSL Configuration**
If you need manual SSL configuration, update `docker/Caddyfile.production`:

```caddyfile
# Custom SSL configuration
https://api.hey.sh {
    tls /path/to/cert.pem /path/to/key.pem
    reverse_proxy localhost:8002
}
```

## 🐳 Docker Deployment

### **Docker Compose Services**
```yaml
# docker/docker-compose.yml
services:
  temporal:
    image: temporalio/auto-setup:latest
    ports:
      - "7233:7233"
  
  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
  
  neo4j:
    image: neo4j:5
    ports:
      - "7474:7474"
      - "7687:7687"
  
  weaviate:
    image: semitechnologies/weaviate:latest
    ports:
      - "8082:8082"
  
  redis:
    image: redis:7
    ports:
      - "6379:6379"
  
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
```

### **Production Dockerfile**
```dockerfile
# Multi-stage build for production
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY src/ ./src/

CMD ["uvicorn", "src.service.api:app", "--host", "0.0.0.0", "--port", "8002"]
```

## 🔧 Environment Configuration

### **Required Environment Variables**
```bash
# Application
HEY_ENV=production
HEY_HTTPS=true

# Database
DATABASE_URL=postgresql://user:password@db.hey.sh:5432/heysh
REDIS_URL=redis://redis.hey.sh:6379
NEO4J_URI=bolt://neo4j.hey.sh:7687
WEAVIATE_URL=https://weaviate.hey.sh

# Temporal
TEMPORAL_ADDRESS=temporal.hey.sh:7233
TEMPORAL_NAMESPACE=default

# Supabase
SUPABASE_URL=https://supabase.hey.sh
SUPABASE_KEY=your-supabase-key

# AI APIs
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
OPEN_ROUTER_API_KEY=your-openrouter-key
```

### **Secrets Management**
```bash
# Use environment variables for secrets
export OPENAI_API_KEY="your-secret-key"
export SUPABASE_KEY="your-supabase-key"

# Or use a secrets management system
# AWS Secrets Manager, HashiCorp Vault, etc.
```

## 📊 Monitoring Setup

### **Start Monitoring Services**
```bash
just monitoring
```

### **Monitoring Configuration**
```yaml
# docker/docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
  
  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
  
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"
  
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
```

## 🔒 Security Configuration

### **Database Security**
- **PostgreSQL**: Use authentication and restrict network access
- **Redis**: Use authentication and restrict network access
- **Neo4j**: Use authentication and restrict network access
- **Weaviate**: Use authentication and restrict network access
- **MinIO**: Use authentication and restrict network access

### **API Security**
- **JWT Authentication**: All API endpoints require authentication
- **Rate Limiting**: Implement rate limiting for API endpoints
- **CORS Configuration**: Proper CORS policies for cross-origin requests
- **Input Validation**: Pydantic schemas for all inputs

### **Network Security**
- **HTTPS Everywhere**: All communications encrypted
- **Firewall Rules**: Restrict access to necessary ports only
- **VPN Access**: Use VPN for administrative access
- **Security Headers**: Implement security headers in Caddy

## 🚀 Kubernetes Deployment

### **GKE Autopilot Configuration**
```yaml
# deployments/k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: heysh-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: heysh-api
  template:
    metadata:
      labels:
        app: heysh-api
    spec:
      containers:
      - name: api
        image: gcr.io/your-project/heysh-api:latest
        ports:
        - containerPort: 8002
        env:
        - name: HEY_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: heysh-secrets
              key: database-url
```

### **Service Configuration**
```yaml
# deployments/k8s/api-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: heysh-api-service
spec:
  selector:
    app: heysh-api
  ports:
  - port: 80
    targetPort: 8002
  type: LoadBalancer
```

## 🔄 CI/CD Pipeline

### **GitHub Actions Workflow**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t gcr.io/${{ secrets.GCP_PROJECT }}/heysh-api:${{ github.sha }} .
    
    - name: Push to GCR
      run: docker push gcr.io/${{ secrets.GCP_PROJECT }}/heysh-api:${{ github.sha }}
    
    - name: Deploy to GKE
      run: |
        gcloud container clusters get-credentials ${{ secrets.GKE_CLUSTER }}
        kubectl set image deployment/heysh-api api=gcr.io/${{ secrets.GCP_PROJECT }}/heysh-api:${{ github.sha }}
```

## ✅ Deployment Checklist

### **Pre-Deployment**
- [ ] DNS records configured
- [ ] SSL certificates ready (Caddy handles this)
- [ ] Environment variables set
- [ ] Database migrations run
- [ ] Security policies configured
- [ ] Monitoring setup
- [ ] Backup strategy implemented

### **Post-Deployment**
- [ ] All services accessible via hostnames
- [ ] SSL certificates working
- [ ] Monitoring services running
- [ ] Alerts configured
- [ ] Performance testing completed
- [ ] Security audit completed

## 🔧 Troubleshooting

### **Common Issues**
1. **DNS Resolution**: Check DNS records are propagated
2. **SSL Certificates**: Verify Caddy is generating certificates
3. **Service Connectivity**: Check all services are running
4. **Database Connections**: Verify database credentials
5. **Monitoring**: Check monitoring services are accessible

### **Debug Commands**
```bash
# Check service status
just verify

# View logs
just logs

# Check DNS resolution
nslookup api.hey.sh

# Test SSL certificates
openssl s_client -connect api.hey.sh:443
```

## 📈 Performance Optimization

### **Scaling Strategies**
- **Horizontal Scaling**: Multiple API server instances
- **Database Scaling**: Read replicas and connection pooling
- **Caching**: Redis for frequently accessed data
- **CDN**: Static asset delivery

### **Monitoring Metrics**
- **Response Times**: API endpoint performance
- **Error Rates**: 4xx and 5xx error rates
- **Resource Usage**: CPU, memory, disk usage
- **Database Performance**: Query performance and connection counts

---

This deployment guide provides everything you need to deploy Hey.sh to production with proper security, monitoring, and scalability.
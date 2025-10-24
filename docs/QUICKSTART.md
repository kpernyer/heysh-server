# Quick Start Guide

Komma igång med Hey.sh local development environment på 5 minuter.

## ✅ Förutsättningar

- Docker & Docker Compose
- `/etc/hosts` uppdaterad med .hey.local entries (se `SETUP_HOSTS.md`)
- `vite.config.ts` uppdaterad (redan gjort ✅)

## 🚀 Start Services

```bash
# Start all services
docker-compose up -d

# Verify all are running
docker-compose ps
```

## 📍 Access Services

### Option 1: Direct Access (Rekommenderat)

**Frontend (Vite Dev Server)**
```
http://localhost:5173
```

**Backend API**
```
http://localhost:8000
http://localhost:8000/health
```

**Monitoring**
```
Prometheus:   http://localhost:9090
Grafana:      http://localhost:3001  (admin/admin)
Jaeger:       http://localhost:16686
Alertmanager: http://localhost:9093
Loki:         http://localhost:3100
```

**Data Services**
```
Temporal UI:  http://localhost:8080
Neo4j:        http://localhost:7474
Weaviate:     http://localhost:8082 (port conflict workaround)
```

### Option 2: Via .hey.local (Requires DNS)

Om du har uppdaterat `/etc/hosts`:

```
http://hey.local              (Frontend)
http://api.hey.local          (API)
http://grafana.hey.local      (Grafana)
http://monitoring.hey.local   (Prometheus)
```

## 🎯 Common Tasks

### Check API Health

```bash
curl http://localhost:8000/health/ready
```

### View Backend Logs

```bash
docker-compose logs -f api
```

### Reload Caddy (After Config Changes)

```bash
docker-compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```

### Open Dashboard

```bash
# View all services in one place
open docs/LOCAL_SERVERS.html
```

## 📊 Monitoring

### Prometheus - Query Metrics

1. Open http://localhost:9090
2. Click "Graph"
3. Try queries like:
   ```promql
   rate(http_requests_total[5m])
   node_memory_MemAvailable_bytes
   ```

### Grafana - Create Dashboards

1. Open http://localhost:3001
2. Login: admin / admin
3. Settings → Data Sources
4. Create new dashboard

### Jaeger - View Traces

1. Open http://localhost:16686
2. Select service and operation
3. View request flow through services

## 🔧 Troubleshooting

### "Blocked request" Error

**Cause**: Vite not allowing the hostname

**Solution**: Already fixed! Make sure you have latest `vite.config.ts`:
```bash
git pull origin main
```

### Port Already in Use

**Cause**: Old containers still running

**Solution**:
```bash
# List all containers
docker ps -a

# Remove old ones
docker rm <container-id>

# Restart
docker-compose up -d
```

### DNS Not Working (.hey.local)

**Solution**:
```bash
# Verify /etc/hosts is updated
grep "hey.local" /etc/hosts

# Clear DNS cache (macOS)
sudo dscacheutil -flushcache

# Test
ping grafana.hey.local
```

### Caddy Returning 308 Redirect

**Cause**: HTTPS redirect still active

**Solution**: Already fixed! Ensure Caddyfile has:
```
{
  auto_https off
  ...
}
```

Restart Caddy:
```bash
docker-compose restart caddy
```

## 📚 Documentation

- **All Servers**: Open `docs/LOCAL_SERVERS.html` in browser
- **Port Mappings**: Read `docs/PORT_MAPPING.md`
- **Monitoring Guide**: Read `docs/MONITORING_LEARNING_GUIDE.md`
- **Kubernetes Health**: Read `docs/KUBERNETES_HEALTH_CHECKS.md`
- **DNS Setup**: Read `docs/SETUP_HOSTS.md`

## 🎓 Learning Path

1. **Start Here** → This file (QUICKSTART.md)
2. **Open Dashboard** → `docs/LOCAL_SERVERS.html`
3. **Try Monitoring** → `docs/MONITORING_LEARNING_GUIDE.md`
4. **Understand Ports** → `docs/PORT_MAPPING.md`
5. **Deploy to Kubernetes** → `docs/KUBERNETES_HEALTH_CHECKS.md`

## ✨ Next Steps

### Test the API

```bash
# Get backend info
curl http://localhost:8000/api/v1/info

# Check health
curl http://localhost:8000/health/ready

# Test Temporal
docker-compose logs temporal | grep "started"
```

### Try Monitoring

1. Open Grafana: http://localhost:3001
2. Add Prometheus datasource
3. Create a simple graph of `up`
4. View Prometheus: http://localhost:9090

### Deploy Locally with Kubernetes

See `docs/KUBERNETES_HEALTH_CHECKS.md` for:
- Pod health probes
- Self-healing configuration
- Deployment examples

## 🆘 Still Having Issues?

1. Check `docker-compose logs service-name`
2. Run `docker-compose ps` to see all services
3. Verify ports aren't in use: `lsof -i :PORT`
4. Read relevant documentation file above

All services are running! You're ready to develop. 🚀

# Local Health Checks and Container Self-Tests

Guide för att testa Kubernetes health checks lokalt med Docker och docker-compose.

## Snabb Start

### 1. Bygg och kör containers lokalt

```bash
# Bygg alla images
docker-compose build

# Starta tjänsterna
docker-compose up -d
```

### 2. Kolla container health status

```bash
# Se hälsostatus för alla containers
docker-compose ps

# Detaljerad status för en container
docker inspect --format='{{.State.Health.Status}}' hey-sh-workflow-api-1
```

## Health Check Endpoints

### API Server (`localhost:8000`)

```bash
# Basic health check
curl http://localhost:8000/health
# {"status": "healthy"}

# Startup probe
curl http://localhost:8000/health/startup
# {
#   "started": true,
#   "timestamp": "2024-01-15T10:30:00Z",
#   "system": {
#     "hostname": "container-id",
#     "environment": "development",
#     "pod_name": "development"
#   },
#   "checks": {
#     "temporal": {"status": "healthy"},
#     "databases": {"status": "healthy"},
#     "services": {"status": "degraded", "issues": ["..."]}
#   }
# }

# Readiness probe
curl http://localhost:8000/health/ready

# Liveness probe
curl http://localhost:8000/health/live
```

### Workers (`localhost:8080`)

```bash
# Port forward worker health check
kubectl port-forward svc/hey-sh-workers 8080:8080

# Or use docker-compose
docker-compose exec general-worker curl http://localhost:8080/health

# Check all worker endpoints
curl http://localhost:8080/health/startup
curl http://localhost:8080/health/ready
curl http://localhost:8080/health/live
```

## Docker HEALTHCHECK Status

### View Container Health

```bash
# Se hälsostatus för alla containers
docker ps --format "table {{.Names}}\t{{.State}}\t{{.Status}}"

# Exempel output:
# NAMES                     STATE     STATUS
# hey-sh-api                running   Up 2 minutes (healthy)
# hey-sh-general-worker     running   Up 2 minutes (healthy)
# hey-sh-ai-worker          running   Up 2 minutes (starting)
```

### Container Health Events

```bash
# Se hälso-events i real-time
docker events --filter type=container --filter event=health_status

# Exempel: När en container blir unhealthy
# 2024-01-15T10:30:00.000000000Z container health_status: unhealthy hey-sh-api-1 (...)
```

### View Health Check Details

```bash
# Se HEALTHCHECK configuration och senaste resultat
docker inspect hey-sh-api-1 | jq '.State.Health'

# Output:
# {
#   "Status": "healthy",
#   "FailingStreak": 0,
#   "Log": [
#     {
#       "Start": "2024-01-15T10:30:00.000000000Z",
#       "End": "2024-01-15T10:30:00.500000000Z",
#       "ExitCode": 0,
#       "Output": ""
#     }
#   ]
# }
```

## Testa Health Check Failures

### Simulera API Server Failure

```bash
# Stäng av API servern inuti containern
docker-compose exec api kill 1

# Kolla container status (bör bli unhealthy efter några sekunder)
watch -n 1 'docker ps --format "table {{.Names}}\t{{.Status}}"'

# Container bör bli "unhealthy" och senare starta om
```

### Simulera Database Connection Failure

```bash
# Stäng av PostgreSQL
docker-compose pause postgres

# API health check bör visa degraderad status
curl http://localhost:8000/health/ready
# {"ready": false, ...}

# Återtag PostgreSQL
docker-compose unpause postgres
```

### Simulera Temporal Failure

```bash
# Stäng av Temporal
docker-compose stop temporal

# Kolla liveness probe (bör misslyckas)
curl http://localhost:8000/health/live
# {"alive": false, ...}

# Container bör starta om enligt liveness probe
```

## Övervaka Health Checks

### Real-time Health Monitoring

```bash
# Övervaka container status
watch -n 1 'docker inspect hey-sh-api-1 | jq ".State.Health"'

# Övervaka alla containers
watch -n 1 'docker ps --format "table {{.Names}}\t{{.Status}}"'

# Övervaka health check logs
docker logs -f hey-sh-api-1 --tail 20
```

### Detaljerad Health Analys

```bash
# Kolla alla HEALTHCHECK resultat
docker inspect hey-sh-api-1 | jq '.State.Health.Log[] | {Start, ExitCode, Output}'

# Räkna failures
docker inspect hey-sh-api-1 | jq '.State.Health.FailingStreak'

# Senaste check tid
docker inspect hey-sh-api-1 | jq '.State.Health.Log[-1].End'
```

## Docker Compose Health Checks

### Exempel docker-compose.yml med HEALTHCHECK

```yaml
services:
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

  general-worker:
    build:
      context: ./backend
      dockerfile: deployments/Dockerfile
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

## Felsökning

### Containern är "Unhealthy"

**Symtom:** `docker ps` visar `(unhealthy)`

**Lösning:**
```bash
# Kolla health check logs
docker inspect hey-sh-api-1 | jq '.State.Health.Log[-3:]'

# Se container logs
docker logs hey-sh-api-1 | tail -50

# Testa health endpoint manuellt
curl http://localhost:8000/health/ready
```

### Health Check Timeout

**Symtom:** Många failures, container blink healthy/unhealthy

**Lösning:**
1. Öka `timeoutSeconds` i probe configuration
2. Kontrollera container resurser (CPU/minne)
3. Kontrollera nätverksanslutning till databaser

### Container Restart Loop

**Symtom:** `docker ps` visar `Restarting` eller `Exited`

**Lösning:**
```bash
# Se varför den startade om
docker logs hey-sh-api-1 --tail 50

# Kontrollera liveness probe
curl http://localhost:8000/health/live

# Öka startup probe timeout
```

## Integration med Kubernetes

Health checks konfigureras här:
- **API:** `k8s/api/deployment.yaml`
- **Workers:** `k8s/workers/deployment.yaml`

Samma endpoints används:
- `/health/startup` - initialisering
- `/health/ready` - ready för trafik
- `/health/live` - liveness

## Best Practices

✅ **GÖR:**
- Kontrollera health status regelbundet
- Övervaka health check logs
- Testa failure scenarios
- Öka timeouts för långsamma operationer

❌ **GÖR INTE:**
- Ignorera `unhealthy` status
- Sätt allt för aggressiva timeouts (<3s)
- Felsök utan att kolla logs
- Ändra health endpoints utan tester

## Relaterad Dokumentation

- [Kubernetes Health Checks](./KUBERNETES_HEALTH_CHECKS.md)
- [Docker HEALTHCHECK Docs](https://docs.docker.com/engine/reference/builder/#healthcheck)
- [Kubernetes Probe Docs](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

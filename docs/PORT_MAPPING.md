# Port och Host Mapping Guide

Allt trafik går genom **Caddy reverse proxy** på port 80/443. Interna tjänster exponerar sina egna portar.

## 🌐 Public URLs (via Caddy)

| Service | URL | Internal Port |
|---------|-----|---|
| **Frontend (React)** | http://hey.local | 5173 |
| **Backend API** | http://api.hey.local | 8000 |
| **Temporal UI** | http://temporal.hey.local | 8080 |
| **Neo4j Browser** | http://neo4j.hey.local | 7474 |
| **Weaviate UI** | http://weaviate.hey.local | 8080 |
| **Database Admin** | http://db.hey.local | 5050 |
| **Prometheus** | http://monitoring.hey.local | 9090 |
| **Grafana** | http://grafana.hey.local | 3001 |
| **Alertmanager** | http://alertmanager.hey.local | 9093 |
| **Jaeger** | http://jaeger.hey.local | 16686 |
| **Loki** | http://loki.hey.local | 3100 |

## 🔧 Internal Ports (Container to Container)

### Core Services

| Service | Container Port | Host Port | Purpose |
|---------|---|---|---|
| API | 8000 | 8000 | FastAPI server |
| Temporal | 7233 | 7233 | Workflow engine |
| Temporal UI | 8080 | 8080 | Temporal web console |
| Neo4j | 7687 | 7687 | Neo4j bolt protocol |
| Neo4j Browser | 7474 | 7474 | Neo4j web interface |
| Weaviate | 8080 | 8080 | Vector database API |
| PostgreSQL | 5432 | 5432 | Database (internal only) |
| Minio | 9000-9001 | 9000-9001 | Object storage |

### Worker Services

| Service | Container Port | Host Port | Purpose |
|---------|---|---|---|
| General Worker | 8080 | (via network) | Health/metrics |
| AI Worker | 8080 | (via network) | Health/metrics |
| Storage Worker | 8080 | (via network) | Health/metrics |

### Monitoring Stack

| Service | Container Port | Host Port | Purpose |
|---------|---|---|---|
| Prometheus | 9090 | 9090 | Metrics collection |
| Grafana | 3000 | 3001 | Dashboards |
| Alertmanager | 9093 | 9093 | Alert management |
| Jaeger | 16686 | 16686 | Distributed tracing |
| Loki | 3100 | 3100 | Log aggregation |
| Node Exporter | 9100 | 9100 | System metrics |
| Promtail | 9080 | (internal) | Log collector |

## 📋 Design Principles

### ✅ DO

1. **Via Caddy för public URLs**
   ```
   User → Caddy (80/443) → localhost:port
   ```

2. **One port per service**
   - API: 8000
   - Temporal: 7233
   - Prometheus: 9090
   - Grafana: 3001 (not 3000)

3. **Internal communication via container names**
   ```yaml
   api:
     environment:
       TEMPORAL_ADDRESS: temporal:7233  # Not localhost
       NEO4J_URI: bolt://neo4j:7687
   ```

4. **Always update Caddyfile when adding new services**
   ```
   newservice.hey.local {
       reverse_proxy localhost:9999
   }
   ```

5. **Health checks on same port as service**
   ```
   curl localhost:8000/health     # API
   curl localhost:9090/api/v1/    # Prometheus
   curl localhost:3001/api/       # Grafana
   ```

### ❌ DON'T

1. **Don't use ports that are already taken**
   - Check existing mappings
   - Use next available port
   - Update documentation

2. **Don't hardcode localhost in container communication**
   ```yaml
   # ❌ WRONG
   TEMPORAL_ADDRESS: localhost:7233

   # ✅ RIGHT
   TEMPORAL_ADDRESS: temporal:7233
   ```

3. **Don't expose monitoring ports directly**
   ```yaml
   # ✅ Only via Caddy (docker-compose.yml)
   ports:
     - "9090:9090"  # Prometheus accessible for internal tools

   # But in documentation, recommend using Caddy URLs
   ```

4. **Don't forget to update docker-compose AND Caddyfile**

## 🔄 How to Add a New Service

### Step 1: Choose Port
Check available ports in this document. Next free port in each range:
- 8000-8099: API layer (8000, 8001, 8002 taken)
- 9000-9099: Storage/utilities (9000, 9001 taken)
- 7000-7999: Databases (7233, 7474, 7687 taken)

### Step 2: Add to docker-compose.yml
```yaml
newservice:
  ports:
    - "9050:9050"  # New service
  networks:
    - temporal-network
```

### Step 3: Update Caddyfile
```
newservice.hey.local {
    reverse_proxy localhost:9050
    encode gzip
}
```

### Step 4: Reload Caddy
```bash
docker-compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```

### Step 5: Update this document
Add entry to relevant section.

## 🧪 Testing Connectivity

### From Host Machine
```bash
# Via Caddy (recommended)
curl http://api.hey.local/health

# Direct (for debugging)
curl http://localhost:8000/health
```

### Between Containers
```bash
# Inside a container
docker-compose exec api curl http://temporal:7233

# Check DNS resolution
docker-compose exec api nslookup temporal
```

### Verify Caddy Routing
```bash
# See all routes
docker-compose exec caddy caddy list-routes

# Check a specific route
curl -I http://api.hey.local
```

## 🚨 Troubleshooting Port Conflicts

### Port Already in Use

```bash
# Find what's using the port
lsof -i :9090

# Kill the process (if safe)
kill -9 <PID>

# Or use different port and update docker-compose + Caddyfile
```

### Service Not Accessible via Caddy

1. **Check service is running**
   ```bash
   docker-compose ps | grep prometheus
   ```

2. **Check direct port works**
   ```bash
   curl http://localhost:9090/api/v1/query
   ```

3. **Reload Caddy**
   ```bash
   docker-compose exec caddy caddy reload --config /etc/caddy/Caddyfile
   ```

4. **Check Caddy logs**
   ```bash
   docker-compose logs caddy
   ```

## 📐 Port Ranges

### Reserved Ranges (Don't Use)

| Range | Usage |
|-------|-------|
| 1-1023 | System ports |
| 5000-5100 | Node.js apps |
| 5173 | Vite dev server |
| 8000-8100 | API/services |
| 9000-9100 | Storage/monitoring |

### Available for Future

| Range | Purpose |
|-------|---------|
| 8100-8200 | Future APIs |
| 9100-9200 | Future monitoring |
| 10000-10100 | Future services |

## 🔐 Networking

### Network Isolation

```yaml
networks:
  temporal-network:   # Temporal + API + Workers
  database-network:   # PostgreSQL + Neo4j + Weaviate
  monitoring:         # Prometheus + Grafana + Loki + Jaeger
```

Services can only reach networks they're connected to.

### Cross-Network Communication

If service A needs to reach service B on different network:

```yaml
serviceA:
  networks:
    - temporal-network
    - monitoring  # Add second network

serviceB:
  networks:
    - monitoring
```

## 📝 Quick Reference

```bash
# Start everything
docker-compose up -d

# Reload Caddy after changes
docker-compose exec caddy caddy reload --config /etc/caddy/Caddyfile

# See all services and ports
docker-compose ps

# Check what's on a port
lsof -i :9090

# Test a service
curl http://api.hey.local/health
curl http://monitoring.hey.local  # Prometheus

# View Caddy config
docker-compose exec caddy cat /etc/caddy/Caddyfile
```

# Hostname-Based Development Setup

## 🎯 Philosophy

**Use hostnames, NOT port numbers**

✅ **Correct**: `http://api.hey.local`
❌ **Wrong**: `http://localhost:8002`

### Why?

1. **Your services own their ports** - Port 8002 is YOUR backend, highest priority
2. **No port conflicts** - If something's on 8002, it's an earlier version of your service
3. **Same code everywhere** - `http://api.hey.local` locally, `https://api.hey.sh` in production
4. **Professional** - Looks like real URLs, not debug ports

---

## 🌐 Service URLs

### Core Application
```
Frontend:    http://hey.local
             http://www.hey.local

Backend API: http://api.hey.local
```

### Infrastructure
```
Temporal UI:     http://temporal.hey.local

Database:        db.hey.local:5432
                 (Local Postgres, Supabase in production)

Neo4j:           http://neo4j.hey.local
Weaviate:        http://weaviate.hey.local
Redis:           http://redis.hey.local

Storage (S3):    http://storage.hey.local
                 (MinIO locally, Supabase Storage in production)
```

### Developer Tools (Local Only)
```
MinIO Console:   http://minio-console.hey.local
```

### Monitoring (Optional)
```
Prometheus:   http://monitoring.hey.local
Grafana:      http://grafana.hey.local
Jaeger:       http://jaeger.hey.local
```

---

## 🔧 How It Works

### Caddy Reverse Proxy

Caddy runs in Docker and provides hostname-based routing:

```
┌─────────────────┐
│  Your Browser   │
│ api.hey.local   │
└────────┬────────┘
         │
    ┌────▼────────┐
    │   Caddy     │  (Port 80/443)
    │  :80 :443   │
    └────┬────────┘
         │
    ┌────▼────────────────┐
    │  Your Backend API   │  (Port 8002)
    │  localhost:8002     │
    └─────────────────────┘
```

**Caddy Configuration**: `docker/Caddyfile`

### DNS Resolution

Add to `/etc/hosts`:

```bash
# Hey.sh Local Development
127.0.0.1  hey.local
127.0.0.1  www.hey.local
127.0.0.1  api.hey.local
127.0.0.1  temporal.hey.local
127.0.0.1  neo4j.hey.local
127.0.0.1  weaviate.hey.local
127.0.0.1  redis.hey.local
127.0.0.1  db.hey.local
127.0.0.1  storage.hey.local
127.0.0.1  minio-console.hey.local
```

**Setup automatically**: `just bootstrap` adds these for you

---

## 📝 Environment Configuration

### Local Development (`.env.local`)

```bash
ENVIRONMENT=local
API_URL=http://api.hey.local
TEMPORAL_ADDRESS=temporal.hey.local:7233

# Abstracted services (implementation hidden)
DATABASE_URL=postgresql://temporal:temporal@db.hey.local:5432/heysh  # Local Postgres
STORAGE_URL=http://storage.hey.local  # MinIO locally

# Specialized databases
NEO4J_URI=bolt://neo4j.hey.local:7687
WEAVIATE_URL=http://weaviate.hey.local
```

### Production (`.env.production`)

```bash
ENVIRONMENT=production
API_URL=https://api-blwol5d45q-ey.a.run.app
TEMPORAL_ADDRESS=your-namespace.tmprl.cloud:7233

# Abstracted services (different providers)
DATABASE_URL=postgresql://user:pass@db.your-project.supabase.co:5432/postgres  # Supabase
STORAGE_URL=https://your-project.supabase.co/storage/v1  # Supabase Storage

# Specialized databases
NEO4J_URI=bolt://your-neo4j-cloud.com:7687
WEAVIATE_URL=https://your-weaviate-cloud.com
```

**Same code, different config!**

---

## 🚀 Usage

### Start Development

```bash
just dev
```

**Automatically:**
1. ✅ Starts Docker
2. ✅ Starts Caddy (PRIORITY #1)
3. ✅ Starts infrastructure (Temporal, Neo4j, etc.)
4. ✅ Loads `.env.local`
5. ✅ Starts your backend on port 8002
6. ✅ Makes everything accessible via hostnames

**Access:**
- Your backend: `http://api.hey.local`
- Not: ~~`http://localhost:8002`~~

### Check Status

```bash
just status
```

**Shows:**
```
🌐 Caddy (Hostname Routing) - PRIORITY #1:
  ✅ Caddy is running (port 80/443)
     Hostnames: *.hey.local → services

🔧 Backend API:
  ✅ http://api.hey.local - healthy
     (via Caddy → localhost:8002)

📦 Infrastructure Services:
  ✅ Infrastructure: 3 services
     Access via: http://temporal.hey.local
                http://neo4j.hey.local
                http://weaviate.hey.local
```

---

## 💻 Code Configuration

### In Your Backend Code

**DON'T hardcode URLs:**
```python
# ❌ Bad - hardcoded port
TEMPORAL_ADDRESS = "localhost:7233"

# ✅ Good - from environment
TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS")
```

**Use environment variables:**
```python
# src/config.py
import os

class Config:
    ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

    # API
    API_URL = os.getenv("API_URL", "http://api.hey.local")

    # Temporal
    TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "temporal.hey.local:7233")

    # Neo4j
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j.hey.local:7687")

    # Weaviate
    WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate.hey.local")

    @classmethod
    def is_local(cls):
        return cls.ENVIRONMENT == "local"

    @classmethod
    def is_production(cls):
        return cls.ENVIRONMENT == "production"
```

**Usage:**
```python
from src.config import Config

# Connect to Temporal
client = await Client.connect(Config.TEMPORAL_ADDRESS)

# Same code works locally AND in production!
```

---

## 🔍 Troubleshooting

### Caddy Not Running?

```bash
# Check
docker ps | grep caddy

# Fix
just fix

# Or manually
docker-compose -f docker/docker-compose.yml up -d caddy
```

### Can't Access api.hey.local?

**Check /etc/hosts:**
```bash
cat /etc/hosts | grep hey.local
```

**Should see:**
```
127.0.0.1  api.hey.local
```

**Add if missing:**
```bash
echo "127.0.0.1  api.hey.local" | sudo tee -a /etc/hosts
```

### Port 8002 Conflict?

**Check what's on 8002:**
```bash
lsof -i :8002
```

**Kill it:**
```bash
kill -9 $(lsof -t -i:8002)
```

**Philosophy:** If something's on port 8002, it's YOUR earlier backend. Kill it!

### Caddy Won't Start?

**Check Caddyfile syntax:**
```bash
docker run --rm -v $(pwd)/docker/Caddyfile:/etc/caddy/Caddyfile caddy:2-alpine caddy validate --config /etc/caddy/Caddyfile
```

**Check logs:**
```bash
docker logs $(docker ps -q -f name=caddy)
```

---

## 🎯 Port Ownership Philosophy

### Your Ports (HIGHEST PRIORITY)

**Port 8002** - Your backend API
**Port 3000** - Your frontend (if local)

**These are YOURS. Nothing else uses them.**

If something's on these ports:
1. It's your earlier version
2. Kill it: `lsof -i :8002` → `kill -9 <PID>`
3. Start fresh: `just dev`

### Infrastructure Ports (via Caddy)

**Port 80** - Caddy HTTP
**Port 443** - Caddy HTTPS

**Everything else accessed via Caddy hostnames.**

---

## 🌍 Production Setup

In production, same philosophy:

**Local:**
```bash
API_URL=http://api.hey.local  # via Caddy
```

**Production:**
```bash
API_URL=https://api-blwol5d45q-ey.a.run.app  # Cloud Run
```

**Same code:**
```python
# This works everywhere!
api_url = Config.API_URL
```

---

## 📚 Quick Reference

```bash
# Start with Caddy + hostnames
just dev

# Check Caddy status
just status

# Access services
open http://api.hey.local
open http://temporal.hey.local
open http://neo4j.hey.local

# Fix if broken
just fix

# Show all hostnames
cat docker/Caddyfile | grep "hey.local"
```

---

## ✅ Checklist

Before you start coding:

- [ ] `/etc/hosts` has `*.hey.local` entries
- [ ] Caddy is running: `docker ps | grep caddy`
- [ ] Backend accessible: `curl http://api.hey.local/health`
- [ ] `.env.local` exists with hostnames (not localhost:port)
- [ ] Code uses `Config.API_URL` not hardcoded URLs

---

**Philosophy Summary:**

1. **Caddy is CRITICAL** - Provides hostname routing
2. **Use hostnames** - `api.hey.local` not `localhost:8002`
3. **You own port 8002** - Highest priority, no conflicts
4. **Config-driven** - Same code, different environments
5. **Professional** - Looks real, works everywhere

**Access your API:**
✅ `http://api.hey.local`
❌ ~~`http://localhost:8002`~~

---

**Last Updated:** 2025-01-29
**See Also:** `DAILY_WORKFLOW.md`, `justfile`

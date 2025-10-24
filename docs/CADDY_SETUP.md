# Caddy Local Development Setup

This guide will help you set up Caddy as a reverse proxy for hey.sh development, replacing port-based URLs with clean local domain names.

## Overview

Instead of accessing services via ports:
- ~~http://localhost:8081~~ → **http://hey.local** (Frontend)
- ~~http://localhost:8000~~ → **http://api.hey.local** (Backend API)
- ~~http://localhost:8233~~ → **http://temporal.hey.local** (Temporal UI)
- ~~http://localhost:7474~~ → **http://neo4j.hey.local** (Neo4j Browser)
- ~~http://localhost:8080~~ → **http://weaviate.hey.local** (Weaviate)

## Prerequisites

- Docker and Docker Compose installed
- `just` command runner installed (optional but recommended)
  ```bash
  # macOS
  brew install just

  # Linux
  cargo install just
  ```

## Setup Steps

### 1. Update `/etc/hosts`

Add local domain entries to your hosts file:

**Option A: Using justfile (recommended)**
```bash
just hosts-setup
```

**Option B: Manual setup**
```bash
sudo nano /etc/hosts
```

Add these lines:
```
# hey.sh local development domains
127.0.0.1 hey.local
127.0.0.1 api.hey.local
127.0.0.1 temporal.hey.local
127.0.0.1 neo4j.hey.local
127.0.0.1 weaviate.hey.local
127.0.0.1 db.hey.local
127.0.0.1 supabase.hey.local
```

### 2. Configure Environment Variables

Copy the example environment file:
```bash
cp .env.example .env.local
```

Update with your Supabase credentials:
```bash
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_TEMPORAL_ADDRESS=localhost:7233
VITE_TEMPORAL_NAMESPACE=default
```

### 3. Start All Services

**Recommended for local development:**
```bash
# Start infrastructure (Caddy, Temporal, Neo4j, Weaviate, Postgres)
just docker-up

# In a separate terminal, start frontend dev server
pnpm run dev
```

**Alternative using justfile shortcut:**
```bash
# Start infrastructure + frontend in one command
just dev-full
```

**Note:** Running `pnpm run dev` directly provides better hot reload performance than Docker. The Dockerfile.dev is kept for CI/CD purposes.

### 4. Verify Services

Check that all services are running:
```bash
just health-check
```

Or manually visit:
- Frontend: http://hey.local
- Temporal UI: http://temporal.hey.local
- Neo4j Browser: http://neo4j.hey.local (username: `neo4j`, password: `password`)
- Weaviate: http://weaviate.hey.local/v1/.well-known/ready

## Available Commands

```bash
# Show all available commands
just

# Start all services
just docker-up

# Stop all services
just docker-down

# View logs
just docker-logs

# View logs for specific service
just docker-logs-service caddy

# Restart services
just docker-restart

# Clean slate (stop and remove volumes)
just docker-clean

# Start frontend dev server only
just dev

# Check service health
just health-check

# Show running containers
just ps
```

## Caddy-Specific Commands

```bash
# Validate Caddy configuration
just caddy-validate

# Reload Caddy configuration (after editing Caddyfile)
just caddy-reload

# Start Caddy standalone (without Docker)
just caddy-start

# Stop Caddy standalone
just caddy-stop
```

## Troubleshooting

### Port conflicts
If you get port conflict errors, check if services are already running:
```bash
# Check what's using port 80 (Caddy)
lsof -i :80

# Check what's using port 8081 (frontend)
lsof -i :8081
```

### Caddy not starting
Validate the Caddyfile syntax:
```bash
just caddy-validate
# or
caddy validate --config Caddyfile
```

### Services not accessible via domain names
1. Verify `/etc/hosts` entries:
   ```bash
   cat /etc/hosts | grep hey.local
   ```

2. Check Caddy logs:
   ```bash
   just docker-logs-service caddy
   ```

3. Verify services are running:
   ```bash
   just ps
   ```

### DNS cache issues
Clear DNS cache (macOS):
```bash
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

## Cleanup

To remove local domain entries from `/etc/hosts`:
```bash
just hosts-cleanup
```

To stop all services and remove volumes:
```bash
just docker-clean
```

## Architecture

```
Browser Request (http://hey.local)
         ↓
    Caddy Reverse Proxy (Port 80)
         ↓
    Frontend Dev Server (Port 8081)
```

All services run in Docker containers on the `hey-network` bridge network, allowing them to communicate with each other using container names.

## Development Workflow

### Starting your day
```bash
# Terminal 1: Start infrastructure (Postgres, Neo4j, Weaviate, Temporal, Caddy)
just docker-up

# Terminal 2: Start frontend (better performance than Docker)
just dev
# or: pnpm run dev

# Terminal 3: Start backend API (better performance than Docker)
just dev-api
# or: cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Access at:**
- Frontend: http://hey.local (Caddy → localhost:8081)
- Backend API: http://api.hey.local (Caddy → localhost:8000)
- Temporal UI: http://temporal.hey.local
- Neo4j Browser: http://neo4j.hey.local

### Ending your day
```bash
# Stop infrastructure
just docker-down

# Stop frontend + backend (Ctrl+C in their terminals)
```

### Making changes to Caddyfile
```bash
# Edit Caddyfile
nano Caddyfile

# Validate changes
just caddy-validate

# Reload configuration
just caddy-reload
```

## Notes

- Caddy automatically handles HTTPS with local certificates (self-signed)
- Frontend hot module reloading (HMR) works through the reverse proxy
- Backend API calls should use `http://api.hey.local` from frontend
- Temporal client connects directly to `localhost:7233` (not through Caddy)

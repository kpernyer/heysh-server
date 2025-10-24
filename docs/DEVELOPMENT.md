# Local Development Guide - Hey.sh

Complete guide to setting up and running Hey.sh locally with all services.

## Prerequisites

- Docker & Docker Compose (v2.0+)
- Node.js 20+ (for frontend)
- Python 3.12
- `just` command runner
- GCP credentials (for Temporal Cloud in production)

## Quick Start

### 0. Configure Local Hostnames

Add these entries to `/etc/hosts` to use real domain names instead of ports:

```bash
# Add to /etc/hosts
127.0.0.1 hey.local
127.0.0.1 api.hey.local
127.0.0.1 temporal.hey.local
127.0.0.1 neo4j.hey.local
127.0.0.1 weaviate.hey.local
127.0.0.1 db.hey.local
```

**Or use the setup script:**
```bash
just hosts-setup
```

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/kpernyer/hey-sh-workflow.git
cd hey-sh-workflow

# Copy environment variables
cp .env.example .env
# Edit .env with your Supabase credentials
```

### 2. Start All Services (with Caddy)

```bash
# Start complete local environment (Temporal, Neo4j, Weaviate, Postgres, API, Workers)
docker-compose up

# Or use justfile
just docker-up

# View Temporal UI
open http://temporal.hey.local

# View Weaviate playground
open http://weaviate.hey.local
```

### 3. Start Frontend (separate terminal)

```bash
# Install dependencies
pnpm install

# Start dev server
pnpm run dev

# Open in browser
open http://hey.local
```

### 4. Test API

```bash
# Health check
curl http://api.hey.local/health

# List workflows
curl http://api.hey.local/api/v1/workflows
```

## Service Details

### Backend API Server (via Caddy)

- **URL**: http://api.hey.local
- **Direct**: http://localhost:8000 (without Caddy)
- **Docs**: http://api.hey.local/docs
- **Health**: http://api.hey.local/health

### Temporal (via Caddy)

- **UI**: http://temporal.hey.local
- **Direct**: http://localhost:8080 (without Caddy)
- **Server**: localhost:7233

### Workers

Three Temporal worker types running:

1. **AI Worker** (`ai-worker`)
   - Processes: Document analysis, LLM calls
   - Queue: `ai-processing-queue`

2. **Storage Worker** (`storage-worker`)
   - Processes: Database operations, indexing
   - Queue: `storage-queue`

3. **General Worker** (`general-worker`)
   - Processes: Coordination, validation
   - Queue: `general-queue`

### Databases (via Caddy)

- **PostgreSQL** (Temporal state): localhost:5432 (direct only)
- **Neo4j** (Graph DB): http://neo4j.hey.local (via Caddy)
  - Browser: http://neo4j.hey.local
  - Direct Bolt: localhost:7687
- **Weaviate** (Vector DB): http://weaviate.hey.local (via Caddy)
  - Direct: http://localhost:8090

### Caddy Reverse Proxy

- **Status**: http://localhost:2019/status (Caddy admin)
- **Config**: ./Caddyfile (auto-reloads on changes)

## Common Commands

### Using Just

```bash
# Setup environment
just setup

# Development servers
just dev              # Frontend only
just dev-api         # Backend only
just docker-up       # All services

# Testing
just test            # Frontend tests
just lint            # Frontend linting
just verify          # Verify environments

# Utilities
just clean           # Clean environments
just verify          # Verify setup
just python          # Python REPL with imports
just run-py script   # Run Python script

# See all commands
just --list
```

### Docker Compose

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f api
docker-compose logs -f ai-worker

# Restart specific service
docker-compose restart storage-worker

# Remove volumes (clean slate)
docker-compose down -v
```

### Testing Workflows

```bash
# Start development environment
docker-compose up

# In another terminal, test workflow execution
python -c "
from temporalio.client import Client
import asyncio

async def main():
    client = await Client.connect('localhost:7233')
    result = await client.execute_workflow(
        'DocumentProcessingWorkflow',
        args=['test-doc-id', 'test-domain', '/path/to/file'],
        id='test-workflow-1',
        task_queue='storage-queue'
    )
    print(f'Result: {result}')

asyncio.run(main())
"
```

## Caddy Configuration

### Local Hostnames Setup

Caddy provides real domain names instead of port numbers for cleaner local development:

**Default Hostnames**:
- `hey.local` → Frontend (Vite dev server)
- `api.hey.local` → Backend API (FastAPI)
- `temporal.hey.local` → Temporal UI
- `neo4j.hey.local` → Neo4j Browser
- `weaviate.hey.local` → Weaviate UI

### Configure /etc/hosts

Add these entries to `/etc/hosts`:

```bash
# macOS / Linux
sudo vim /etc/hosts

# Add these lines:
127.0.0.1 hey.local
127.0.0.1 api.hey.local
127.0.0.1 temporal.hey.local
127.0.0.1 neo4j.hey.local
127.0.0.1 weaviate.hey.local
127.0.0.1 db.hey.local
```

Or use the justfile:
```bash
just hosts-setup
```

### Caddy Commands

```bash
# Start Caddy separately
just caddy-start

# Stop Caddy
just caddy-stop

# Reload Caddy config (after editing Caddyfile)
just caddy-reload

# Validate Caddyfile syntax
just caddy-validate
```

### Edit Caddyfile

To add more hostnames or change routing:

```bash
vim Caddyfile
# Make changes, then:
just caddy-reload
```

**Example**: Add a new service
```caddyfile
# PostgreSQL Admin
pgadmin.hey.local {
    reverse_proxy localhost:5050
    encode gzip
}
```

## Debugging

### View Service Logs

```bash
# Backend API logs
docker-compose logs -f api

# Temporal server logs
docker-compose logs -f temporal

# Specific worker logs
docker-compose logs -f ai-worker
docker-compose logs -f storage-worker
docker-compose logs -f general-worker

# All database logs
docker-compose logs -f postgres neo4j weaviate
```

### Connect to Databases

```bash
# PostgreSQL
psql -h localhost -U temporal -d temporal

# Neo4j
neo4j cypher-shell -a neo4j://localhost:7687 -u neo4j -p password

# Weaviate GraphQL
curl http://weaviate.hey.local/v1/graphql -X POST \
  -H "Content-Type: application/json" \
  -d '{"query": "{ Aggregate { Document { meta { count } } } }"}'
```

### Temporal CLI Commands

```bash
# List namespaces
tctl namespace list

# List task queues
tctl task-queue list

# View workflow execution
tctl workflow show -w workflow-id

# Check queue stats
tctl task-queue describe -task-queue storage-queue

# Monitor activities
tctl activity ls -task-queue ai-processing-queue
```

## Development Workflow

### 1. Modify Code

```bash
# Edit backend code
vim backend/service/routes_auth.py

# The API auto-reloads with Uvicorn
# Just refresh your browser or API client
```

### 2. Run Tests

```bash
# Run backend structure tests
just run-py -m pytest backend/test/structure/ -v

# Run linting
just lint

# Fix linting issues
pnpm run lint --fix
```

### 3. Test Workflows

```bash
# Start Python shell with imports ready
just python

# Then in Python REPL:
>>> await client.execute_workflow(...)
```

### 4. Commit Changes

```bash
# Check status
git status

# Stage changes
git add .

# Commit (pre-commit hooks run automatically)
git commit -m "feat: add new workflow"

# Push
git push origin feature-branch
```

## Production Preview

To preview how services behave in production:

```bash
# Build production images
docker-compose -f docker-compose.yml build

# Deploy locally with Terraform (dry-run)
cd terraform/prod
terraform plan -var-file=terraform.tfvars

# Run production smoke tests
python backend/test/smoke_test_staging.py
```

## Troubleshooting

### Containers won't start

```bash
# Check disk space
docker system df

# Clean up
docker system prune -a
docker volume prune

# Recreate
docker-compose down -v
docker-compose up
```

### Port conflicts

```bash
# Check what's using port 8000
lsof -i :8000

# Kill process or change docker-compose port mapping
```

### Database connection errors

```bash
# Verify PostgreSQL is healthy
docker-compose exec postgres pg_isready

# Check Neo4j connectivity
docker-compose exec neo4j cypher-shell -u neo4j -p password "RETURN 1"
```

### Workers not processing tasks

```bash
# Verify worker is connected to Temporal
docker-compose logs ai-worker | grep "connected"

# Check task queue
tctl task-queue describe -task-queue ai-processing-queue

# Manually register worker
docker-compose restart ai-worker
```

## Environment Variables

See `.env.example` for all variables:

- **Supabase**: URL, API key, JWT secret
- **Neo4j**: User, password
- **OpenAI**: API key for embeddings
- **Anthropic**: API key for Claude
- **Temporal Cloud**: Address, namespace, certs (production only)

## Performance Tips

1. **Monitor resource usage**:
   ```bash
   docker stats
   ```

2. **Optimize database queries**:
   - Use Neo4j UI at http://neo4j.hey.local
   - Monitor Weaviate at http://weaviate.hey.local

3. **Scale workers**:
   - Increase replicas in docker-compose
   - Monitor queue backlog with `tctl task-queue describe`

4. **Profile code**:
   ```bash
   just python  # Use py-spy for profiling
   ```

## Next Steps

1. ✅ Local development running
2. 🔧 Modify backend/frontend as needed
3. 📝 Write tests
4. 🚀 Deploy to staging
5. ✨ Deploy to production (via Terraform)

See [WORKERS.md](./WORKERS.md) for queue configuration details.

---

**Last Updated**: October 21, 2025
**Status**: Production Ready

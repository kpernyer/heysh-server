# Temporal Cloud - Quick Start

✅ **Your system is now configured for Temporal Cloud!**

## What Was Configured

### 1. Environment Variables (`.env`)
```bash
TEMPORAL_ADDRESS='europe-west3.gcp.api.temporal.io:7233'
TEMPORAL_NAMESPACE='quickstart-heysh-knowledge.jnw2m'
TEMPORAL_API_KEY='eyJhbGc...'  # Your API key
TEMPORAL_TASK_QUEUE='hey-sh-workflows'
```

### 2. Code Updates
- ✅ `service/api.py` - Auto-detects Cloud vs Local, adds TLS
- ✅ `worker/main.py` - Auto-detects Cloud vs Local, adds TLS
- ✅ Both support seamless switching between local/cloud

### 3. Helper Scripts
- ✅ `script/start_api_cloud.sh` - Start API with Temporal Cloud
- ✅ `script/start_worker_cloud.sh` - Start worker with Temporal Cloud

## Quick Commands

### Start Services (Temporal Cloud)

```bash
# Terminal 1: Start worker
cd backend
./script/start_worker_cloud.sh

# Terminal 2: Start API
cd backend
./script/start_api_cloud.sh
```

### Or Manually

```bash
# Worker
cd backend
set -a && source .env && set +a
.venv/bin/python worker/main.py

# API
cd backend
set -a && source .env && set +a
.venv/bin/uvicorn service.api:app --reload --port 8001
```

## Verify Connection

You should see:
```
Starting Temporal worker address=europe-west3.gcp.api.temporal.io:7233
Using Temporal Cloud with TLS and API key authentication ✓
Worker started successfully. Waiting for tasks...
```

## View Workflows

- **Temporal Cloud UI:** https://cloud.temporal.io
- **Namespace:** `quickstart-heysh-knowledge.jnw2m`

## Switch to Local Development

To use local Temporal (Docker):

```bash
# 1. Comment out or remove TEMPORAL_API_KEY in .env
# TEMPORAL_API_KEY=

# 2. Update address
TEMPORAL_ADDRESS=localhost:7233
TEMPORAL_NAMESPACE=default

# 3. Start local Temporal
just dev

# 4. Start worker & API (will auto-detect local mode)
```

## Documentation

- Full setup guide: `docs/TEMPORAL_CLOUD_SETUP.md`
- How it works, deployment, troubleshooting, etc.

## Current Status

✅ **Worker:** Connected to Temporal Cloud
✅ **API:** Ready to use Temporal Cloud
✅ **Auto-detection:** Switches based on `TEMPORAL_API_KEY`
✅ **Scripts:** Helper scripts created

**Next:** Run workflows and view them in Temporal Cloud dashboard!

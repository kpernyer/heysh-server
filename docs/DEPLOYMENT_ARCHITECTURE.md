# Hey.sh Production Architecture

## 🌐 Live System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRODUCTION SYSTEM                         │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│   Frontend (Live)    │
│  ─────────────────   │
│  Platform: Lovable   │
│  URL: www.hey.sh     │
│  SSL: ✅ Active      │
└──────────┬───────────┘
           │
           │ HTTPS
           │
┌──────────▼───────────────────────────────────────────────────┐
│                    Backend (To Deploy)                        │
│  ────────────────────────────────────────────────────────    │
│  Platform: Google Cloud Run (europe-west3)                   │
│  Services:                                                    │
│    • FastAPI Backend API (hey-sh-backend)                    │
│    • Temporal Worker (hey-sh-worker)                         │
└──────────┬────────────────────────────┬─────────────────────┘
           │                            │
           │                            │
┌──────────▼────────────┐    ┌─────────▼──────────────────────┐
│  Orchestration (✅)   │    │     Databases (✅)              │
│  ─────────────────    │    │  ────────────────────────────  │
│  Temporal Cloud       │    │  • Neo4j Aura (Graph DB)       │
│  europe-west3.gcp     │    │  • Weaviate Cloud (Vector DB)  │
│  Namespace: jnw2m     │    │  • Supabase (SQL/Auth/Storage) │
└───────────────────────┘    └────────────────────────────────┘
```

## 📊 Component Details

### Frontend - Lovable.dev
- **URL:** http://www.hey.sh
- **Platform:** Lovable.dev (managed deployment)
- **Framework:** React + Vite
- **SSL:** Automatic HTTPS
- **CDN:** Global edge network
- **Cost:** Included in Lovable.dev subscription

**Environment Variables (to set in Lovable.dev):**
```bash
VITE_SUPABASE_URL=https://dnpdqilxauylnjtysqmo.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=eyJhbGci...
VITE_API_URL=<BACKEND_URL>  # Set after deploying backend
```

### Backend API - Cloud Run (Pending)
- **Service:** hey-sh-backend
- **Region:** europe-west3 (Frankfurt)
- **Framework:** FastAPI + Uvicorn
- **Port:** 8000
- **Scaling:** 0-10 instances (auto-scale)
- **Memory:** 512MB
- **CPU:** 1 core
- **Cost:** ~$10-20/month

**Key Endpoints:**
- `GET /health` - Health check
- `POST /api/domains` - Create domain workflow
- `GET /api/domains/{id}` - Get domain details
- `POST /api/documents/process` - Process document

### Temporal Worker - Cloud Run (Pending)
- **Service:** hey-sh-worker
- **Region:** europe-west3 (Frankfurt)
- **Task Queue:** hey-sh-workflows
- **Scaling:** 1-10 instances (min 1 for availability)
- **Memory:** 1GB
- **CPU:** 1 core
- **Cost:** ~$20/month

**Workflows:**
- Domain creation workflow
- Document processing workflow
- Knowledge graph building workflow

### Temporal Cloud - ✅ Live
- **Provider:** Temporal Cloud
- **Region:** europe-west3.gcp.api.temporal.io
- **Namespace:** quickstart-heysh-knowledge.jnw2m
- **Authentication:** API key (TLS)
- **Cost:** $200/month (or free tier)

**Features:**
- Durable execution
- Workflow versioning
- Activity retry logic
- Workflow history
- Monitoring dashboard

### Neo4j Aura - ✅ Live
- **Provider:** Neo4j Aura
- **URI:** neo4j+s://2e747e38.databases.neo4j.io
- **Database:** Heysh-workflow
- **Version:** Neo4j 5.27-aura Enterprise
- **Cost:** Free tier (upgrade to $65/mo for production)

**Data Model:**
- Domain nodes
- Document nodes
- Knowledge relationships
- Graph traversal queries

### Weaviate Cloud - ✅ Live
- **Provider:** Weaviate Cloud
- **URL:** https://k763euant8waed9amnzca.c0.europe-west3.gcp.weaviate.cloud
- **Region:** europe-west3 (GCP)
- **Collections:** Domain (with vectors)
- **Cost:** ~$70/month (standard)

**Features:**
- Vector embeddings (OpenAI)
- Semantic search
- Hybrid search (vector + keyword)
- LLM integration for summaries

### Supabase - ✅ Live
- **Provider:** Supabase
- **URL:** https://dnpdqilxauylnjtysqmo.supabase.co
- **Services:** PostgreSQL, Auth, Storage
- **Cost:** $25/month

**Tables:**
- User accounts
- Domain metadata
- Document metadata
- Access control

## 🔒 Security Architecture

### Authentication Flow
```
User → Frontend (www.hey.sh)
         ↓
    Supabase Auth
         ↓
    JWT Token
         ↓
Backend API (validates JWT)
         ↓
Temporal Workflow (triggered)
         ↓
Activities (access databases)
```

### Secrets Management
- **Development:** `.env` file (local)
- **Production:** Google Secret Manager
- **Secrets:**
  - temporal-api-key
  - neo4j-uri, neo4j-password
  - weaviate-url, weaviate-api-key
  - supabase-url, supabase-key
  - openai-api-key

### Network Security
- ✅ All database connections use TLS/SSL
- ✅ Backend API uses HTTPS only
- ✅ Worker not publicly accessible
- ✅ Secrets never in code or logs
- ✅ Service accounts with minimal permissions

## 📈 Data Flow

### Example: Create Domain Workflow

```
1. User submits domain at www.hey.sh
   ↓
2. Frontend → POST /api/domains (Backend API)
   ↓
3. Backend starts Temporal workflow
   ↓
4. Worker executes activities:
   - Create domain in Neo4j
   - Generate embeddings
   - Store vectors in Weaviate
   - Update metadata in Supabase
   ↓
5. Frontend polls for completion
   ↓
6. Display results to user
```

## 💰 Cost Breakdown

| Component | Provider | Monthly Cost | Status |
|-----------|----------|--------------|--------|
| Frontend | Lovable.dev | Included | ✅ Live |
| Backend API | Cloud Run | $10-20 | 🔄 Pending |
| Worker | Cloud Run | $20 | 🔄 Pending |
| Temporal Cloud | Temporal.io | $200 | ✅ Live |
| Neo4j Aura | Neo4j | Free-$65 | ✅ Live |
| Weaviate | Weaviate Cloud | $70 | ✅ Live |
| Supabase | Supabase | $25 | ✅ Live |
| **Total** | | **$325-400** | **85% Complete** |

## 🚀 Deployment Status

### ✅ Completed (85%)
1. Frontend deployed to www.hey.sh
2. Temporal Cloud connected
3. Neo4j Aura connected and tested
4. Weaviate Cloud connected and tested
5. Supabase already in cloud
6. Deployment scripts created

### 🔄 Pending (15%)
1. Deploy worker to Cloud Run
2. Deploy backend API to Cloud Run
3. Update frontend API URL in Lovable.dev
4. End-to-end production testing

## 🎯 Next Steps

### Deploy Backend to Cloud Run
```bash
cd backend

# 1. Set GCP project
gcloud config set project YOUR_PROJECT_ID

# 2. Create secrets
./script/setup_gcp_secrets.sh

# 3. Deploy worker
./script/deploy_worker.sh

# 4. Deploy API
./script/deploy_backend.sh
```

### Update Frontend
```bash
# In Lovable.dev dashboard:
# 1. Go to Environment Variables
# 2. Update VITE_API_URL to backend URL from step 4
# 3. Redeploy frontend
```

### Test Production
```bash
# 1. Open www.hey.sh
# 2. Create a domain
# 3. Verify workflow executes
# 4. Check Temporal Cloud dashboard
# 5. Verify data in Neo4j Aura console
```

## 📊 Monitoring & Observability

### Temporal Cloud
- Dashboard: https://cloud.temporal.io
- Workflow history
- Activity execution logs
- Error rates and retries

### Cloud Run
- Logs: `gcloud run logs read SERVICE_NAME`
- Metrics: CPU, memory, request count
- Error tracking
- Performance monitoring

### Databases
- Neo4j Aura Console: https://console.neo4j.io
- Weaviate Cloud Dashboard
- Supabase Dashboard

### Frontend
- Lovable.dev Analytics
- Browser console errors
- User session tracking

## 🔧 Operations

### Scaling
- **Frontend:** Auto-scaled by Lovable CDN
- **Backend API:** Auto-scales 0-10 instances
- **Worker:** Auto-scales 1-10 instances (min 1)
- **Databases:** Managed scaling by providers

### Backup & Recovery
- **Neo4j:** Automated daily backups
- **Weaviate:** Managed backups
- **Supabase:** Point-in-time recovery
- **Temporal:** Workflow history retained

### Updates
- **Frontend:** Deploy via Lovable.dev
- **Backend:** Redeploy Cloud Run services
- **Databases:** Managed updates
- **Secrets:** Update via Secret Manager

---

**Architecture Version:** 1.0
**Last Updated:** 2025-10-17
**Status:** 85% Cloud Migration Complete
**Production URL:** http://www.hey.sh

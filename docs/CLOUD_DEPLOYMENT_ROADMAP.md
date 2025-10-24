# Cloud Deployment Roadmap

## Current State Analysis

### ✅ Already in Cloud
- **Temporal Orchestration:** Temporal Cloud (europe-west3.gcp)
- **Supabase:** Cloud-hosted (database, auth, storage)

### ⚠️ Running Locally (Need to Deploy)
1. **Temporal Worker** - Python process (connects to Temporal Cloud)
2. **FastAPI Backend** - Python/Uvicorn server
3. **Neo4j** - Graph database (Docker)
4. **Weaviate** - Vector database (Docker)
5. **Frontend** - React/Vite app (Docker)
6. **Reverse Proxy** - Caddy (Docker)

## Deployment Priority & Strategy

### Phase 1: Core Services (Critical Path)

#### 1. Deploy Neo4j to Cloud ⭐ PRIORITY
**Why:** Required by all workflows, stateful data

**Options:**
- **Neo4j Aura** (Managed, Recommended)
  - Fully managed Neo4j cloud
  - Auto-scaling, backups, monitoring
  - Europe region available
  - Cost: ~$65/mo (small instance)

- **Google Cloud Marketplace Neo4j**
  - Self-managed on GCP
  - More control, more ops work

**Recommendation:** Use Neo4j Aura for production

**Setup:**
```bash
# 1. Sign up: https://neo4j.com/cloud/aura/
# 2. Create database (Europe region)
# 3. Get connection string
# 4. Update .env:
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
```

#### 2. Deploy Weaviate to Cloud ⭐ PRIORITY
**Why:** Required for semantic search, stateful data

**Options:**
- **Weaviate Cloud Services** (Managed, Recommended)
  - Fully managed Weaviate
  - Auto-scaling, backups
  - OpenAI integration built-in
  - Cost: ~$25/mo (sandbox), ~$70/mo (standard)

- **Google Cloud Marketplace Weaviate**
  - Self-managed on GCP

**Recommendation:** Use Weaviate Cloud Services

**Setup:**
```bash
# 1. Sign up: https://console.weaviate.cloud
# 2. Create cluster (Europe region)
# 3. Get API endpoint and key
# 4. Update .env:
WEAVIATE_URL=https://xxxxx.weaviate.network
WEAVIATE_API_KEY=your-api-key
```

#### 3. Deploy Temporal Worker ⭐ PRIORITY
**Why:** No workflows run without workers

**Options:**
- **Cloud Run** (Recommended for simplicity)
  - Serverless, auto-scaling
  - Pay per use
  - Easy deployment

- **GKE** (For high throughput)
  - More control
  - Better for many concurrent workflows

**Recommendation:** Start with Cloud Run, move to GKE if needed

**Dockerfile (already exists at `backend/docker/Dockerfile`):**
```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY . .
RUN pip install -e .

CMD ["python", "worker/main.py"]
```

**Deploy to Cloud Run:**
```bash
# Build and push
gcloud builds submit --tag gcr.io/YOUR_PROJECT/hey-sh-worker

# Deploy
gcloud run deploy hey-sh-worker \
  --image gcr.io/YOUR_PROJECT/hey-sh-worker \
  --region europe-west3 \
  --platform managed \
  --no-allow-unauthenticated \
  --min-instances 1 \
  --max-instances 10 \
  --set-env-vars TEMPORAL_ADDRESS=europe-west3.gcp.api.temporal.io:7233 \
  --set-secrets TEMPORAL_API_KEY=temporal-api-key:latest \
  --set-secrets NEO4J_URI=neo4j-uri:latest \
  --set-secrets WEAVIATE_URL=weaviate-url:latest
```

#### 4. Deploy FastAPI Backend ⭐ PRIORITY
**Why:** Frontend needs API to trigger workflows

**Deploy to Cloud Run:**
```bash
# Build and push
gcloud builds submit --tag gcr.io/YOUR_PROJECT/hey-sh-backend

# Deploy
gcloud run deploy hey-sh-backend \
  --image gcr.io/YOUR_PROJECT/hey-sh-backend \
  --region europe-west3 \
  --platform managed \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars TEMPORAL_ADDRESS=europe-west3.gcp.api.temporal.io:7233 \
  --set-secrets TEMPORAL_API_KEY=temporal-api-key:latest
```

### Phase 2: Frontend & Additional Services

#### 5. Deploy Frontend
**Options:**
- **Vercel** (Recommended for Vite/React)
- **Netlify**
- **Cloud Storage + CDN**
- **Cloud Run**

**Recommendation:** Vercel for simplicity

**Setup:**
```bash
# 1. Connect repo to Vercel
# 2. Set build command: npm run build
# 3. Set environment variables
# 4. Deploy
```

#### 6. Setup Secrets Management
**Google Secret Manager:**
```bash
# Create secrets
gcloud secrets create temporal-api-key --data-file=- <<EOF
your-temporal-api-key
EOF

gcloud secrets create neo4j-uri --data-file=- <<EOF
neo4j+s://xxxxx.databases.neo4j.io
EOF

gcloud secrets create openai-api-key --data-file=- <<EOF
sk-...
EOF

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding temporal-api-key \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Deployment Checklist

### Pre-Deployment
- [ ] Neo4j Aura database created and configured
- [ ] Weaviate Cloud cluster created and configured
- [ ] Secrets created in Google Secret Manager
- [ ] Docker images built and pushed to GCR
- [ ] Environment variables documented

### Core Deployment
- [ ] Temporal Worker deployed to Cloud Run
- [ ] FastAPI Backend deployed to Cloud Run
- [ ] Verify worker connects to Temporal Cloud
- [ ] Verify API can trigger workflows
- [ ] Test end-to-end workflow execution

### Frontend Deployment
- [ ] Frontend deployed to Vercel/Netlify
- [ ] API endpoint updated in frontend config
- [ ] CORS configured in backend
- [ ] Test frontend → backend → workflow flow

### Post-Deployment
- [ ] Monitoring configured (Cloud Logging, Temporal Cloud)
- [ ] Alerts set up for failures
- [ ] Backup strategy verified (Neo4j, Weaviate)
- [ ] Load testing completed
- [ ] Documentation updated

## Cost Estimates (Monthly)

### Minimal Production Setup
| Service | Provider | Cost |
|---------|----------|------|
| Temporal Cloud | Temporal | $200 (free tier available) |
| Neo4j Aura | Neo4j | $65 |
| Weaviate Cloud | Weaviate | $70 |
| Cloud Run (Worker) | GCP | $10-50 |
| Cloud Run (API) | GCP | $10-50 |
| Supabase | Supabase | $25 (Pro plan) |
| Frontend (Vercel) | Vercel | $0 (Hobby) or $20 (Pro) |
| **Total** | | **~$380-$480/mo** |

### Scaling Considerations
- Neo4j: Scale to larger instance as data grows
- Weaviate: Scale to standard tier for production
- Cloud Run: Auto-scales based on load
- Consider GKE for worker if >100 concurrent workflows

## Migration Strategy

### Step-by-Step Migration

**Week 1: Database Migration**
1. Set up Neo4j Aura
2. Export local Neo4j data
3. Import to Aura
4. Test connections
5. Set up Weaviate Cloud
6. Migrate vector data
7. Test semantic search

**Week 2: Worker & Backend**
1. Deploy worker to Cloud Run
2. Verify Temporal Cloud connection
3. Run test workflows
4. Deploy FastAPI backend
5. Verify API endpoints
6. Test workflow triggers

**Week 3: Frontend & Polish**
1. Deploy frontend
2. Update environment configs
3. End-to-end testing
4. Performance testing
5. Set up monitoring

**Week 4: Production Cutover**
1. DNS updates
2. SSL certificates
3. Final testing
4. Go live
5. Monitor closely

## Quick Start Commands

### 1. Set up managed databases
```bash
# Neo4j Aura: https://console.neo4j.io
# Weaviate Cloud: https://console.weaviate.cloud
```

### 2. Create secrets
```bash
./script/setup_secrets.sh  # Create this script
```

### 3. Build and deploy worker
```bash
cd backend
gcloud builds submit --tag gcr.io/YOUR_PROJECT/hey-sh-worker --config=cloudbuild-worker.yaml
```

### 4. Build and deploy API
```bash
cd backend
gcloud builds submit --tag gcr.io/YOUR_PROJECT/hey-sh-backend --config=cloudbuild-api.yaml
```

### 5. Deploy frontend
```bash
cd frontend
vercel deploy --prod
```

## Monitoring & Operations

### Essential Monitoring
1. **Temporal Cloud Dashboard**
   - Workflow success/failure rates
   - Activity execution times
   - Worker health

2. **Cloud Logging**
   - Worker logs
   - API logs
   - Error tracking

3. **Database Monitoring**
   - Neo4j Aura console
   - Weaviate Cloud metrics

### Alerting
Set up alerts for:
- Worker disconnections
- Workflow failures >5%
- API error rate >1%
- Database connection issues
- High latency (>2s)

## Security Checklist
- [ ] All secrets in Secret Manager (not .env)
- [ ] IAM roles properly scoped
- [ ] VPC for database access
- [ ] API authentication enabled
- [ ] HTTPS enforced everywhere
- [ ] CORS properly configured
- [ ] Rate limiting on API
- [ ] Secrets rotation policy

## Rollback Plan

### If Production Issues
1. **Immediate:** Switch traffic back to local
2. **Database:** Restore from backup
3. **Worker:** Roll back to previous image
4. **API:** Roll back to previous image
5. **Frontend:** Revert Vercel deployment

### Backup Strategy
- Neo4j: Daily automated backups (Aura)
- Weaviate: Snapshots every 6 hours (Cloud)
- Code: Git tags for each deployment
- Config: Terraform state in GCS

## Next Steps

### Immediate (This Week)
1. **Sign up for Neo4j Aura** - Get database URL
2. **Sign up for Weaviate Cloud** - Get cluster endpoint
3. **Create GCP secrets** - Store all API keys securely

### Short-term (Next 2 Weeks)
1. **Deploy worker to Cloud Run** - Test workflow execution
2. **Deploy API to Cloud Run** - Test API endpoints
3. **Migrate data** - Move Neo4j and Weaviate data to cloud

### Medium-term (Next Month)
1. **Deploy frontend** - Full production deployment
2. **Set up monitoring** - Dashboards and alerts
3. **Load testing** - Verify scalability
4. **Documentation** - Update all docs with production URLs

## Resources

### Documentation
- Temporal Cloud: https://docs.temporal.io/cloud
- Neo4j Aura: https://neo4j.com/docs/aura
- Weaviate Cloud: https://weaviate.io/developers/wcs
- Cloud Run: https://cloud.google.com/run/docs

### Your Infrastructure
- Terraform configs: `backend/infra/terraform/`
- Kubernetes manifests: `backend/infra/k8s/`
- Docker configs: `backend/docker/`

### Support
- Temporal: cloud-support@temporal.io
- Neo4j: support@neo4j.com
- Weaviate: support@weaviate.io

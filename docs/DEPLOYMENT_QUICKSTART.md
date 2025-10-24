# Cloud Deployment - Quick Start

## 📊 What Needs to Move to Cloud

### ✅ Already Cloud (Done!)
```
✓ Temporal Orchestration → Temporal Cloud (europe-west3)
✓ Database/Auth/Storage → Supabase
```

### 🚀 Needs Deployment (Your To-Do)

```
Priority 1 (Critical - Must Deploy):
├── 1. Neo4j Database      → Neo4j Aura (~$65/mo)
├── 2. Weaviate Vectors    → Weaviate Cloud (~$70/mo)
├── 3. Temporal Worker     → Cloud Run (~$20/mo)
└── 4. FastAPI Backend     → Cloud Run (~$20/mo)

Priority 2 (Can Deploy Later):
└── 5. Frontend           → Vercel/Netlify (Free-$20/mo)
```

**Estimated Total Cost:** ~$195-$215/month

## 🎯 Deployment Order (Step-by-Step)

### Step 1: Deploy Databases (30 min)

**Neo4j:**
```bash
# 1. Go to: https://console.neo4j.io
# 2. Create Aura database (Europe region)
# 3. Copy connection details
# 4. Update .env:
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-generated-password
```

**Weaviate:**
```bash
# 1. Go to: https://console.weaviate.cloud
# 2. Create cluster (Europe region)
# 3. Copy endpoint and API key
# 4. Update .env:
WEAVIATE_URL=https://xxxxx.weaviate.network
WEAVIATE_API_KEY=your-api-key
```

### Step 2: Deploy Temporal Worker (15 min)

```bash
cd backend

# Build Docker image
gcloud builds submit --tag gcr.io/YOUR_PROJECT/hey-sh-worker

# Deploy to Cloud Run
gcloud run deploy hey-sh-worker \
  --image gcr.io/YOUR_PROJECT/hey-sh-worker \
  --region europe-west3 \
  --platform managed \
  --min-instances 1 \
  --set-env-vars TEMPORAL_ADDRESS=europe-west3.gcp.api.temporal.io:7233,TEMPORAL_NAMESPACE=quickstart-heysh-knowledge.jnw2m \
  --set-secrets TEMPORAL_API_KEY=temporal-api-key:latest,NEO4J_URI=neo4j-uri:latest,WEAVIATE_URL=weaviate-url:latest
```

### Step 3: Deploy Backend API (15 min)

```bash
cd backend

# Build Docker image
gcloud builds submit --tag gcr.io/YOUR_PROJECT/hey-sh-backend

# Deploy to Cloud Run
gcloud run deploy hey-sh-backend \
  --image gcr.io/YOUR_PROJECT/hey-sh-backend \
  --region europe-west3 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars TEMPORAL_ADDRESS=europe-west3.gcp.api.temporal.io:7233,TEMPORAL_NAMESPACE=quickstart-heysh-knowledge.jnw2m \
  --set-secrets TEMPORAL_API_KEY=temporal-api-key:latest
```

### Step 4: Deploy Frontend (10 min)

**Option A: Vercel (Recommended)**
```bash
# 1. Install Vercel CLI: npm i -g vercel
# 2. Deploy:
cd /path/to/frontend
vercel deploy --prod

# 3. Set environment variable in Vercel dashboard:
VITE_API_URL=https://your-backend-url.run.app
```

**Option B: Netlify**
```bash
# 1. Connect repo to Netlify
# 2. Build command: npm run build
# 3. Publish directory: dist
```

## ✅ Verification Checklist

After deployment, verify:

```bash
# 1. Worker is running
gcloud run services describe hey-sh-worker --region europe-west3

# 2. API is accessible
curl https://your-backend-url.run.app/health

# 3. Frontend loads
open https://your-frontend-url.vercel.app

# 4. Workflow execution works
# Trigger a test workflow from the UI
```

## 🔑 Secrets Setup (Before Deploying)

Create secrets in Google Secret Manager:

```bash
# Temporal API Key
echo -n "YOUR_TEMPORAL_API_KEY" | gcloud secrets create temporal-api-key --data-file=-

# Neo4j URI
echo -n "neo4j+s://xxxxx.databases.neo4j.io" | gcloud secrets create neo4j-uri --data-file=-

# Weaviate URL
echo -n "https://xxxxx.weaviate.network" | gcloud secrets create weaviate-url --data-file=-

# OpenAI API Key
echo -n "sk-..." | gcloud secrets create openai-api-key --data-file=-

# Grant access to Cloud Run
for secret in temporal-api-key neo4j-uri weaviate-url openai-api-key; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
done
```

## 📈 What You'll Gain

### Before (Local Dev)
```
❌ Dependent on your laptop
❌ Single point of failure
❌ No auto-scaling
❌ Manual restarts needed
❌ Limited to one developer
```

### After (Cloud)
```
✅ Runs 24/7 independently
✅ Auto-scales with load
✅ Automatic restarts/healing
✅ Global accessibility
✅ Team can collaborate
✅ Professional monitoring
```

## 🚨 Common Issues & Fixes

### Worker Not Connecting
```bash
# Check logs
gcloud run logs read hey-sh-worker --region europe-west3 --limit 50

# Verify secrets
gcloud secrets versions access latest --secret="temporal-api-key"
```

### API Returning Errors
```bash
# Check logs
gcloud run logs read hey-sh-backend --region europe-west3 --limit 50

# Test health endpoint
curl https://your-backend-url.run.app/health
```

### Database Connection Failed
```bash
# Verify Neo4j URI format (must include neo4j+s://)
# Verify Weaviate URL (must be https://)
# Check firewall rules allow outbound connections
```

## 📚 Full Documentation

- **Detailed Roadmap:** `backend/docs/CLOUD_DEPLOYMENT_ROADMAP.md`
- **Temporal Cloud:** `backend/docs/TEMPORAL_CLOUD_SETUP.md`
- **Architecture:** `backend/docs/COMPARISON_ANTHROPIC_AGENT_SKILLS.md`

## 💰 Cost Breakdown

| Service | Monthly Cost | Scalability |
|---------|--------------|-------------|
| **Temporal Cloud** | $200 (or free tier) | Auto-scales |
| **Neo4j Aura** | $65 | Upgrade as needed |
| **Weaviate Cloud** | $70 | Auto-scales |
| **Cloud Run Worker** | $20 | Pay per use |
| **Cloud Run API** | $20 | Pay per use |
| **Supabase** | $25 | Included storage |
| **Frontend (Vercel)** | $0-20 | Unlimited |
| **TOTAL** | **~$400/mo** | Scales with usage |

## 🎯 Next Actions (In Order)

1. **Today:** Sign up for Neo4j Aura + Weaviate Cloud
2. **Today:** Create GCP secrets with all credentials
3. **Tomorrow:** Deploy worker to Cloud Run
4. **Tomorrow:** Deploy API to Cloud Run
5. **This Week:** Deploy frontend to Vercel
6. **This Week:** Test end-to-end in production

---

**Ready to deploy?** Start with Step 1 above! 🚀

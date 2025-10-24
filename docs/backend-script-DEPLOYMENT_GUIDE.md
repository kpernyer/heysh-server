# Cloud Deployment Guide

This directory contains scripts to deploy hey-sh to Google Cloud Platform.

## 📋 Prerequisites

1. **GCP Project Setup**
   ```bash
   # Set your GCP project
   gcloud config set project YOUR_PROJECT_ID

   # Verify it's set
   gcloud config get-value project
   ```

2. **Enable Required APIs**
   ```bash
   # Enable Cloud Run, Cloud Build, and Secret Manager
   gcloud services enable run.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable secretmanager.googleapis.com
   ```

3. **Cloud Databases Configured**
   - ✅ Temporal Cloud (already connected)
   - ✅ Neo4j Aura (already connected)
   - ✅ Weaviate Cloud (already connected)
   - ✅ Supabase (already in cloud)

4. **Environment Variables Set**
   - All credentials in `.env` file
   - See `CLOUD_MIGRATION_PROGRESS.md` for checklist

## 🚀 Deployment Steps

### Step 1: Create GCP Secrets

This script reads your `.env` file and creates secrets in Google Secret Manager:

```bash
cd backend
./script/setup_gcp_secrets.sh
```

**What it does:**
- Creates/updates secrets for all credentials
- Grants access to Cloud Run service account
- Lists all created secrets

**Expected output:**
```
🔐 Setting up GCP Secrets for Hey.sh
📦 Project: your-project-id
✨ Creating new secret: temporal-api-key
   ✅ temporal-api-key configured
...
✅ All secrets configured successfully!
```

### Step 2: Deploy Temporal Worker

This deploys the worker that executes Temporal workflows:

```bash
./script/deploy_worker.sh
```

**What it does:**
- Builds Docker image using `docker/Dockerfile`
- Pushes to Google Container Registry
- Deploys to Cloud Run with:
  - Min 1 instance (always running to process workflows)
  - Max 10 instances (auto-scales under load)
  - 1GB memory, 1 CPU
  - All secrets mounted as environment variables
  - Command: `python worker/main.py`

**Expected output:**
```
🚀 Deploying Temporal Worker to Cloud Run
🔨 Building Docker image...
📦 Deploying to Cloud Run...
✅ Worker deployed successfully!
🌐 Service URL: https://hey-sh-worker-xxx-ew.a.run.app
```

**Important:** The worker runs with `min-instances=1` to ensure it's always ready to process workflows. This costs ~$20/month but ensures zero cold starts.

### Step 3: Deploy Backend API

This deploys the FastAPI backend that triggers workflows:

```bash
./script/deploy_backend.sh
```

**What it does:**
- Builds Docker image using `docker/Dockerfile`
- Pushes to Google Container Registry
- Deploys to Cloud Run with:
  - Min 0 instances (scales to zero when idle)
  - Max 10 instances (auto-scales under load)
  - 512MB memory, 1 CPU
  - All secrets mounted
  - Publicly accessible (for frontend)
  - Command: `uvicorn service.api:app --host 0.0.0.0 --port 8000`

**Expected output:**
```
🚀 Deploying Backend API to Cloud Run
🔨 Building Docker image...
📦 Deploying to Cloud Run...
✅ Backend deployed successfully!
🌐 Service URL: https://hey-sh-backend-xxx-ew.a.run.app

⚠️  Update your frontend .env with:
   VITE_API_URL=https://hey-sh-backend-xxx-ew.a.run.app
```

**Important:** Copy the service URL and update your frontend `.env` file!

## 🧪 Testing Deployments

### Test Worker
```bash
# View worker logs
gcloud run logs read hey-sh-worker --region europe-west3 --limit 50

# Should see:
# "Starting Temporal worker"
# "Using Temporal Cloud with TLS and API key authentication"
# "Worker started successfully. Waiting for tasks..."
```

### Test Backend API
```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe hey-sh-backend --region europe-west3 --format "value(status.url)")

# Test health endpoint
curl $SERVICE_URL/health

# Should return:
# {"status":"healthy","temporal":"connected"}
```

### Test End-to-End Workflow
1. Trigger a workflow from frontend or API
2. Check Temporal Cloud console: https://cloud.temporal.io
3. Verify workflow executes successfully
4. Check worker logs for activity execution

## 📊 Monitoring

### View Logs
```bash
# Worker logs
gcloud run logs read hey-sh-worker --region europe-west3 --limit 100

# Backend logs
gcloud run logs read hey-sh-backend --region europe-west3 --limit 100

# Follow logs in real-time
gcloud run logs tail hey-sh-worker --region europe-west3
```

### View Service Details
```bash
# Worker details
gcloud run services describe hey-sh-worker --region europe-west3

# Backend details
gcloud run services describe hey-sh-backend --region europe-west3

# List all services
gcloud run services list
```

### Cloud Console
- **Cloud Run:** https://console.cloud.google.com/run
- **Secrets:** https://console.cloud.google.com/security/secret-manager
- **Logs:** https://console.cloud.google.com/logs
- **Temporal:** https://cloud.temporal.io

## 🔄 Updating Deployments

### Update Worker
```bash
# Make code changes, then redeploy
./script/deploy_worker.sh
```

### Update Backend
```bash
# Make code changes, then redeploy
./script/deploy_backend.sh
```

### Update Secrets
```bash
# Update .env file, then run
./script/setup_gcp_secrets.sh
```

**Note:** After updating secrets, you must redeploy services for changes to take effect.

## 🛑 Stopping Services

### Delete Worker
```bash
gcloud run services delete hey-sh-worker --region europe-west3
```

### Delete Backend
```bash
gcloud run services delete hey-sh-backend --region europe-west3
```

### Delete Secrets
```bash
# List secrets
gcloud secrets list

# Delete specific secret
gcloud secrets delete SECRET_NAME
```

## 💰 Cost Optimization

### Current Configuration
- **Worker:** ~$20/mo (min-instances=1, always running)
- **Backend:** ~$5-10/mo (scales to zero when idle)
- **Total:** ~$25-30/mo for compute

### Reduce Costs
```bash
# Lower worker min instances (but adds cold start latency)
gcloud run services update hey-sh-worker \
  --region europe-west3 \
  --min-instances 0

# Reduce memory (if usage is low)
gcloud run services update hey-sh-worker \
  --region europe-west3 \
  --memory 512Mi
```

## 🔒 Security

### Best Practices Implemented
- ✅ Secrets in Secret Manager (not environment variables)
- ✅ Non-root user in Docker container
- ✅ Minimal Docker image (python:3.11-slim)
- ✅ Worker not publicly accessible
- ✅ Backend uses HTTPS only
- ✅ Service account with minimal permissions

### Additional Security (Optional)
```bash
# Restrict backend to specific domains
gcloud run services update hey-sh-backend \
  --region europe-west3 \
  --ingress internal-and-cloud-load-balancing

# Enable Cloud Armor for DDoS protection
# See: https://cloud.google.com/armor/docs
```

## 🐛 Troubleshooting

### Worker Not Processing Workflows
1. Check worker is running:
   ```bash
   gcloud run services describe hey-sh-worker --region europe-west3
   ```

2. View logs for errors:
   ```bash
   gcloud run logs read hey-sh-worker --region europe-west3 --limit 50
   ```

3. Verify Temporal connection:
   - Check `TEMPORAL_API_KEY` secret is set
   - Check `TEMPORAL_NAMESPACE` is correct
   - View Temporal Cloud console for worker status

### Backend API Returning Errors
1. Test health endpoint:
   ```bash
   curl https://YOUR-BACKEND-URL/health
   ```

2. Check logs:
   ```bash
   gcloud run logs read hey-sh-backend --region europe-west3 --limit 50
   ```

3. Verify secrets are accessible:
   ```bash
   gcloud secrets list
   gcloud secrets versions access latest --secret="temporal-api-key"
   ```

### Build Failures
1. Check Dockerfile syntax
2. Verify dependencies in `pyproject.toml`
3. Check Cloud Build logs:
   ```bash
   gcloud builds list --limit 10
   gcloud builds log BUILD_ID
   ```

### Permission Denied Errors
1. Enable required APIs:
   ```bash
   gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
   ```

2. Grant permissions to service account:
   ```bash
   # Get service account
   gcloud iam service-accounts list

   # Grant Secret Manager access
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="serviceAccount:SERVICE_ACCOUNT" \
     --role="roles/secretmanager.secretAccessor"
   ```

## 📚 Additional Resources

- **Cloud Run Documentation:** https://cloud.google.com/run/docs
- **Secret Manager:** https://cloud.google.com/secret-manager/docs
- **Temporal Cloud:** https://docs.temporal.io/cloud
- **Deployment Roadmap:** `../docs/CLOUD_DEPLOYMENT_ROADMAP.md`
- **Migration Progress:** `../../CLOUD_MIGRATION_PROGRESS.md`

## 🎯 Next Steps

After deploying worker and backend:

1. **Deploy Frontend to Vercel**
   ```bash
   cd ../../frontend
   vercel deploy --prod
   ```

2. **Set up monitoring and alerts**
   - Configure Cloud Monitoring
   - Set up error rate alerts
   - Monitor costs in Cloud Console

3. **Configure custom domain** (optional)
   - Map custom domain to Cloud Run service
   - Set up SSL certificate

4. **Test production workflows**
   - Run end-to-end tests
   - Verify all integrations work
   - Monitor performance

---

**Questions?** Check the troubleshooting section above or review the full deployment roadmap in `../docs/CLOUD_DEPLOYMENT_ROADMAP.md`.

# Production Deployment Instructions

## Overview

This deployment uses **Terraform** for infrastructure management and **Helm/Kubernetes** for application deployment.

**Architecture:**
- **Backend API** → Google Cloud Run (managed, auto-scaling)
- **Workers** → GKE Autopilot cluster with Helm (3 worker types)
- **Infrastructure** → Managed by Terraform
- **Secrets** → Google Secret Manager

## Quick Deploy

```bash
./deploy_production.sh
```

This script will:
1. ✅ Check prerequisites (gcloud, terraform, helm, kubectl)
2. ✅ Optionally run database migration (Domain → Topic)
3. ✅ Apply Terraform infrastructure
4. ✅ Build Docker images via Cloud Build
5. ✅ Deploy backend to Cloud Run
6. ✅ Deploy workers to GKE via Helm
7. ✅ Verify deployment

## Prerequisites

### 1. Install Required Tools

```bash
# Google Cloud SDK
brew install google-cloud-sdk

# Terraform
brew install terraform

# Helm
brew install helm

# kubectl
gcloud components install kubectl
```

### 2. Authenticate with GCP

```bash
# Login to GCP
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Verify
gcloud config get-value project
```

### 3. Enable Required APIs

```bash
gcloud services enable \
  cloudrun.googleapis.com \
  container.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com
```

## Deployment Steps

### Step 1: Database Migration (One-time)

**IMPORTANT:** Run this BEFORE deploying code changes.

The database migration renames all "domain" terminology to "topic":
- Tables: `domains` → `topics`, `domain_members` → `topic_members`
- Columns: `domain_id` → `topic_id` in all tables
- Foreign keys and indexes updated

**Option A: Via Supabase Dashboard (Recommended)**

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Copy the contents of `migrations/001_rename_domain_to_topic_up.sql`
4. Paste and click **Run**
5. Verify with:
   ```sql
   SELECT table_name FROM information_schema.tables
   WHERE table_name IN ('topics', 'topic_members');
   ```

**Option B: Via psql**

```bash
psql "$SUPABASE_CONNECTION_STRING" < migrations/001_rename_domain_to_topic_up.sql
```

### Step 2: Run Deployment Script

```bash
# Full deployment with migration prompt
./deploy_production.sh

# Skip Terraform if infrastructure unchanged
SKIP_TERRAFORM=true ./deploy_production.sh

# Skip migration prompt
RUN_MIGRATION=false ./deploy_production.sh

# Custom version tag
VERSION=v1.2.3 ./deploy_production.sh
```

### Step 3: Verify Deployment

```bash
# Get backend URL
gcloud run services describe api --region europe-west3 --format="value(status.url)"

# Test health endpoint
curl https://your-api-url.run.app/health

# Test topics endpoint
curl https://your-api-url.run.app/api/v1/topics

# Check worker pods
kubectl get pods -n temporal-workers

# View backend logs
gcloud run logs read api --region europe-west3 --limit 50

# View worker logs
kubectl logs -n temporal-workers -l worker-type=general -f
```

## Deployment Architecture

### Infrastructure (Terraform)

Located in: `infra/terraform/`

**Managed Resources:**
- GKE Autopilot Cluster (for workers)
- Cloud Run Service (for backend API)
- Artifact Registry (Docker images)
- Secret Manager (credentials)
- Service Accounts & IAM
- BigQuery (monitoring)

**Commands:**
```bash
cd infra/terraform

# Initialize
terraform init

# Plan changes
terraform plan \
  -var="project_id=$PROJECT_ID" \
  -var="region=europe-west3" \
  -var="environment=production"

# Apply
terraform apply
```

### Application (Helm)

Located in: `infra/helm/temporal-workers/`

**Worker Types:**
1. **AI Processing** (GPU-enabled)
   - 2-5 replicas
   - 8-16 GB RAM
   - 1 GPU (NVIDIA)
   - For LLM inference

2. **Storage Worker** (Spot instances)
   - 1-10 replicas
   - 2-4 GB RAM
   - Document processing
   - 80% cost savings via Spot

3. **General Worker** (Spot instances)
   - 3-10 replicas
   - 1-2 GB RAM
   - Generic workflows

**Commands:**
```bash
# Get cluster credentials
gcloud container clusters get-credentials production-hey-sh-cluster \
  --region europe-west3

# Deploy workers
helm upgrade --install temporal-workers ./infra/helm/temporal-workers \
  --namespace temporal-workers \
  --create-namespace \
  --set global.projectId="$PROJECT_ID" \
  --set image.tag="latest"

# Check status
kubectl get pods -n temporal-workers
helm list -n temporal-workers
```

## Environment Variables

### Backend API (Cloud Run)

Set via Secret Manager and injected automatically:
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `TEMPORAL_ADDRESS`
- `TEMPORAL_NAMESPACE`
- `TEMPORAL_API_KEY`
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- `WEAVIATE_URL`, `WEAVIATE_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`

### Workers (GKE)

Synced from Secret Manager to Kubernetes secrets via `infra/k8s/sync-secrets.sh`

## Rollback Procedure

### Database Rollback

```bash
# Via Supabase Dashboard
# Run: migrations/001_rename_domain_to_topic_down.sql

# Via psql
psql "$SUPABASE_CONNECTION_STRING" < migrations/001_rename_domain_to_topic_down.sql
```

### Application Rollback

```bash
# Backend (Cloud Run)
gcloud run services update api \
  --image europe-west3-docker.pkg.dev/$PROJECT_ID/hey-sh-backend/service:PREVIOUS_VERSION \
  --region europe-west3

# Workers (Helm)
helm rollback temporal-workers -n temporal-workers
```

## Monitoring

### Cloud Run (Backend)

```bash
# View logs
gcloud run logs read api --region europe-west3 --limit 100

# View metrics
open "https://console.cloud.google.com/run/detail/europe-west3/api"
```

### GKE (Workers)

```bash
# Pod status
kubectl get pods -n temporal-workers

# Logs
kubectl logs -n temporal-workers -l worker-type=ai-processing -f
kubectl logs -n temporal-workers -l worker-type=storage -f
kubectl logs -n temporal-workers -l worker-type=general -f

# Metrics
kubectl top pods -n temporal-workers
```

### Alerts

Configure in GCP Console:
- Cloud Run error rate > 5%
- GKE pod crash loops
- Worker queue backlog > 1000

## Cost Optimization

The deployment is optimized for cost:

1. **Cloud Run** - Pay per request, scales to zero
2. **GKE Autopilot** - Managed, right-sized pods
3. **Spot Instances** - 80% savings for storage/general workers
4. **Auto-scaling** - Scales down during low traffic
5. **GPU workers** - Only when needed

**Estimated costs:**
- Backend API: $10-50/month (depends on traffic)
- Workers (idle): $50-100/month
- Workers (active): $200-500/month
- Total: ~$260-650/month

## Troubleshooting

### "No GCP project configured"

```bash
gcloud config set project YOUR_PROJECT_ID
```

### "Terraform state locked"

```bash
cd infra/terraform
terraform force-unlock LOCK_ID
```

### "Cloud Build failed"

```bash
# Check build logs
gcloud builds list --limit 5
gcloud builds log BUILD_ID
```

### "Workers not starting"

```bash
# Check pod events
kubectl describe pod POD_NAME -n temporal-workers

# Check secrets
kubectl get secrets -n temporal-workers
```

### "Database migration failed"

1. Check Supabase logs
2. Verify table names:
   ```sql
   SELECT table_name FROM information_schema.tables
   WHERE table_schema = 'public';
   ```
3. Rollback if needed:
   ```bash
   # Run down migration
   psql < migrations/001_rename_domain_to_topic_down.sql
   ```

## Security Notes

1. **Secrets** - Never commit secrets to git
2. **IAM** - Use least privilege service accounts
3. **Network** - Workers run in private VPC
4. **Auth** - Backend requires JWT tokens
5. **Encryption** - All data encrypted at rest/transit

## Support

For deployment issues:
1. Check logs (Cloud Run, GKE)
2. Review Terraform state
3. Verify secrets in Secret Manager
4. Check Cloud Build history

Documentation:
- `API_MIGRATION_GUIDE.md` - Frontend integration
- `MIGRATION_QUICKSTART.md` - Database migration
- `ARCHITECTURE_CHANGES_SUMMARY.md` - Full change list

## Deployment Checklist

Before deploying:
- [ ] GCP project configured
- [ ] Required APIs enabled
- [ ] Secrets in Secret Manager
- [ ] Database backup created
- [ ] Frontend team notified

After deploying:
- [ ] Health check passes
- [ ] Topics endpoint works
- [ ] Workers running
- [ ] Logs clean
- [ ] Frontend updated

---

**Last Updated:** 2025-01-28
**Version:** 1.0.0

# Production CI/CD Bootstrap Guide

**Purpose:** Document and preserve the production CI/CD setup so it's repeatable if you ever need to recreate it.

---

## 📋 Quick Check

Run this first to see what's already configured:

```bash
just bootstrap-production
```

This will show you the status of all production infrastructure components.

---

## 🏗️ Complete Production Setup (From Scratch)

If you're setting up production CI/CD from scratch or recreating it, follow these steps:

### 1. GCP Project Setup

```bash
# Set your project
export PROJECT_ID="hey-sh-production"
export REGION="europe-west3"

# Activate project
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  cloudrun.googleapis.com \
  container.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  compute.googleapis.com
```

### 2. Artifact Registry (Docker Images)

```bash
# Create Docker registry for backend images
gcloud artifacts repositories create hey-sh-backend \
  --repository-format=docker \
  --location=$REGION \
  --description="Hey.sh backend and worker images"

# Verify
gcloud artifacts repositories describe hey-sh-backend --location=$REGION
```

### 3. Secret Manager (Credentials)

```bash
# Store secrets (replace with your actual values)
echo -n "your-supabase-url" | gcloud secrets create SUPABASE_URL --data-file=-
echo -n "your-supabase-key" | gcloud secrets create SUPABASE_KEY --data-file=-
echo -n "your-temporal-address" | gcloud secrets create TEMPORAL_ADDRESS --data-file=-
echo -n "your-temporal-namespace" | gcloud secrets create TEMPORAL_NAMESPACE --data-file=-
echo -n "your-temporal-api-key" | gcloud secrets create TEMPORAL_API_KEY --data-file=-
echo -n "your-neo4j-uri" | gcloud secrets create NEO4J_URI --data-file=-
echo -n "your-neo4j-user" | gcloud secrets create NEO4J_USER --data-file=-
echo -n "your-neo4j-password" | gcloud secrets create NEO4J_PASSWORD --data-file=-
echo -n "your-weaviate-url" | gcloud secrets create WEAVIATE_URL --data-file=-
echo -n "your-weaviate-api-key" | gcloud secrets create WEAVIATE_API_KEY --data-file=-
echo -n "your-openai-api-key" | gcloud secrets create OPENAI_API_KEY --data-file=-
echo -n "your-anthropic-api-key" | gcloud secrets create ANTHROPIC_API_KEY --data-file=-

# Verify
gcloud secrets list
```

### 4. Terraform Infrastructure

```bash
cd infra/terraform

# Initialize Terraform (uses GCS backend for state)
terraform init

# Create infrastructure
terraform plan \
  -var="project_id=$PROJECT_ID" \
  -var="region=$REGION" \
  -var="environment=production"

terraform apply \
  -var="project_id=$PROJECT_ID" \
  -var="region=$REGION" \
  -var="environment=production"

cd ../..
```

**This creates:**
- GKE Autopilot Cluster: `production-hey-sh-cluster`
- Cloud Run Service: `api`
- Service Accounts with proper IAM roles
- BigQuery datasets for monitoring

### 5. Cloud Build Triggers (Git-based Deployment)

```bash
# Main production deployment trigger (triggered by git tags: v*)
gcloud builds triggers create github \
  --name=deploy-tag \
  --repo-name=heysh-server \
  --repo-owner=kpernyer \
  --branch-pattern="^main$" \
  --tag-pattern="^v.*" \
  --build-config=cloudbuild_deploy.yaml \
  --substitutions=_REGION=$REGION,_DEPLOY_ENV=production \
  --description="Full production deployment (backend + workers) triggered by version tags"

# Optional: Backend-only trigger (for main branch pushes)
gcloud builds triggers create github \
  --name=deploy-backend-main \
  --repo-name=heysh-server \
  --repo-owner=kpernyer \
  --branch-pattern="^main$" \
  --build-config=cloudbuild_backend.yaml \
  --substitutions=_REGION=$REGION,_DEPLOY_ENV=development \
  --description="Backend-only deployment for main branch"

# Optional: Workers-only trigger (for main branch pushes)
gcloud builds triggers create github \
  --name=build-workers-main \
  --repo-name=heysh-server \
  --repo-owner=kpernyer \
  --branch-pattern="^main$" \
  --build-config=cloudbuild_workers.yaml \
  --substitutions=_REGION=$REGION \
  --description="Workers-only build for main branch"

# Verify triggers
gcloud builds triggers list
```

### 6. Build Custom Helm Builder (for Cloud Build)

Cloud Build needs a custom builder image with Helm + kubectl:

```bash
# Create Dockerfile for Helm builder
cat > /tmp/Dockerfile.helm <<'EOF'
FROM google/cloud-sdk:alpine
RUN apk add --no-cache curl bash
RUN curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
EOF

# Build and push
cd /tmp
docker build -f Dockerfile.helm -t gcr.io/$PROJECT_ID/helm:latest .
docker push gcr.io/$PROJECT_ID/helm:latest

# Verify
gcloud container images list --repository=gcr.io/$PROJECT_ID
```

### 7. GKE Cluster Configuration

```bash
# Get cluster credentials
gcloud container clusters get-credentials production-hey-sh-cluster \
  --region=$REGION

# Create namespace for workers
kubectl create namespace temporal-workers

# Sync secrets from Secret Manager to Kubernetes
./infra/k8s/sync-secrets.sh
```

### 8. Initial Deployment

```bash
# Deploy backend manually first time
gcloud run deploy api \
  --image=europe-west3-docker.pkg.dev/$PROJECT_ID/hey-sh-backend/service:latest \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars="$(gcloud secrets versions access latest --secret=SUPABASE_URL)" \
  --max-instances=10 \
  --cpu=2 \
  --memory=4Gi

# Deploy workers via Helm
helm upgrade --install temporal-workers ./infra/helm/temporal-workers \
  --namespace temporal-workers \
  --set global.projectId=$PROJECT_ID \
  --set global.region=$REGION \
  --set global.environment=production \
  --set image.tag=latest \
  --wait
```

### 9. Verify Everything Works

```bash
# Check production infrastructure
just bootstrap-production

# Should show all ✅:
# ✅ GCP Project
# ✅ Cloud Build Triggers
# ✅ Artifact Registry
# ✅ Cloud Run Service
# ✅ GKE Cluster
# ✅ Secrets

# Check health
just check production
```

---

## 🔄 Daily Usage (After Bootstrap)

Once setup is complete, you **never** need to run these commands again.

Your daily workflow becomes:

```bash
# Local development
just dev

# Deploy to production
just deploy v1.2.3 "Add feature"

# Check status
just check production

# View logs
just logs production backend

# Learn from metrics
just learn
```

**That's it!** Everything else is automated via Cloud Build.

---

## 📊 Architecture Summary

```
Your Laptop                         GitHub                    Google Cloud
────────────                       ────────                  ──────────────

  just deploy         ──push──>    [Repository]   ──webhook──>  Cloud Build
  (creates tag)                    + git tag v1.2.3              │
                                                                 ├─ Build images
                                                                 ├─ Push to Artifact Registry
                                                                 ├─ Deploy to Cloud Run
                                                                 └─ Deploy to GKE via Helm

                                                                 Production:
                                                                 ├─ Cloud Run (API)
                                                                 └─ GKE (Workers)
```

---

## 🔐 Security Notes

### Service Accounts

Terraform creates these service accounts automatically:

- `development-cloudbuild@` - Cloud Build service account
- `api-runtime@` - Cloud Run service account
- `gke-worker@` - GKE worker service account

### IAM Permissions

Each service account has minimal required permissions:

- **Cloud Build**: Build images, deploy to Cloud Run/GKE, read secrets
- **Cloud Run**: Access secrets, write logs
- **GKE Workers**: Access secrets, write logs, connect to Temporal

### Secret Access

Secrets are stored in Secret Manager and injected at runtime:

- **Cloud Run**: Via environment variables
- **GKE**: Via Kubernetes secrets (synced from Secret Manager)

---

## 🧰 Maintenance Commands

### Update Terraform Infrastructure

```bash
cd infra/terraform

# Plan changes
terraform plan \
  -var="project_id=$PROJECT_ID" \
  -var="region=$REGION" \
  -var="environment=production"

# Apply if looks good
terraform apply
```

### Update Secrets

```bash
# Update a secret
echo -n "new-value" | gcloud secrets versions add SUPABASE_KEY --data-file=-

# Redeploy to pick up new secret
just deploy v1.2.4 "Update secrets"
```

### View Cloud Build History

```bash
# Via CLI
gcloud builds list --limit=10

# Via Web
open https://console.cloud.google.com/cloud-build/builds
```

### Check Costs

```bash
# Cloud Run costs
gcloud run services describe api --region=$REGION --format="yaml(status)"

# GKE costs
gcloud container clusters describe production-hey-sh-cluster --region=$REGION

# Full billing (web)
open https://console.cloud.google.com/billing
```

---

## 🚨 Disaster Recovery

### If Cloud Build is Down

Deploy manually:

```bash
# Build image locally
docker build -t europe-west3-docker.pkg.dev/$PROJECT_ID/hey-sh-backend/service:emergency .

# Push to registry
docker push europe-west3-docker.pkg.dev/$PROJECT_ID/hey-sh-backend/service:emergency

# Deploy to Cloud Run
gcloud run services update api \
  --image=europe-west3-docker.pkg.dev/$PROJECT_ID/hey-sh-backend/service:emergency \
  --region=$REGION
```

### If Terraform State is Lost

State is stored in GCS bucket `terraform-state-bucket-{project-id}`.

```bash
# List state files
gsutil ls gs://terraform-state-bucket-$PROJECT_ID/

# Download state
gsutil cp gs://terraform-state-bucket-$PROJECT_ID/default.tfstate .

# Import existing resources
terraform import google_cloud_run_service.api projects/$PROJECT_ID/locations/$REGION/services/api
```

### If You Need to Start Over

1. Export secrets: `gcloud secrets list --format=json > secrets-backup.json`
2. Backup database: Via Supabase Dashboard
3. Destroy: `cd infra/terraform && terraform destroy`
4. Follow "Complete Production Setup" above
5. Restore secrets
6. Run database migrations

---

## 📖 File Reference

### Cloud Build Configs

- `cloudbuild_deploy.yaml` - **Main production deployment** (triggered by git tags)
- `cloudbuild_backend.yaml` - Backend-only deployment
- `cloudbuild_workers.yaml` - Workers-only deployment

### Infrastructure

- `infra/terraform/` - All infrastructure as code
  - `main.tf` - Main resources (GKE, Cloud Run, etc.)
  - `variables.tf` - Configuration variables
  - `outputs.tf` - Output values (URLs, etc.)
- `infra/helm/temporal-workers/` - Helm chart for workers
- `infra/k8s/` - Kubernetes configs

### Deployment Scripts

- `deploy_production.sh` - Manual deployment script (backup)
- `justfile` - **Daily workflow commands**

---

## ✅ Checklist: Is My Production Setup Complete?

Run `just bootstrap-production` and verify:

- [x] GCP Project configured
- [x] Cloud Build Triggers (at least 1)
- [x] Artifact Registry repository exists
- [x] Cloud Run service running
- [x] GKE cluster exists
- [x] Secrets in Secret Manager
- [x] Can deploy: `just deploy v1.0.0 "Test"`
- [x] Can check: `just check production`
- [x] Backend responds: `curl https://api-blwol5d45q-ey.a.run.app/health`

If all ✅, your production CI/CD is ready!

---

## 🎓 Understanding the Flow

1. **You**: `just deploy v1.2.3 "New feature"`
2. **Git**: Creates commit + tag, pushes to GitHub
3. **GitHub**: Sends webhook to Cloud Build
4. **Cloud Build**:
   - Runs `cloudbuild_deploy.yaml`
   - Builds 4 Docker images
   - Pushes to Artifact Registry
   - Deploys backend to Cloud Run
   - Deploys workers to GKE via Helm
5. **Production**: New version is live
6. **You**: `just check production` (verify)

**You never touch terraform, gcloud, kubectl, helm directly.**

---

**Last Updated:** 2025-01-29
**Author:** Production Team
**Next Review:** When infrastructure changes

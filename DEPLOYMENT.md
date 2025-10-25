# Deployment Guide

## Architecture Overview

Our deployment uses the proper separation of concerns:

- **Terraform**: Manages GCP infrastructure (Cloud Run, GKE, Secret Manager, IAM)
- **Helm**: Manages Kubernetes workloads (Temporal workers)
- **Cloud Build**: CI/CD pipeline for building images

## Infrastructure Layers

```
┌─────────────────────────────────────────┐
│         Application Layer                │
│  (Helm Charts - Kubernetes Workloads)   │
│  - Temporal Workers                      │
│  - ConfigMaps, Services                  │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│      Infrastructure Layer                │
│     (Terraform - GCP Resources)          │
│  - GKE Autopilot Cluster                 │
│  - Cloud Run Services                    │
│  - Artifact Registry                     │
│  - Secret Manager                        │
│  - IAM & Service Accounts                │
└─────────────────────────────────────────┘
```

## Deployment Methods

### 1. Manual Deployment (Recommended for first deploy)

```bash
# Full deployment with interactive Terraform approval
./script/deploy.sh

# Backend only
DEPLOY_WORKERS=false ./script/deploy.sh

# Workers only
DEPLOY_BACKEND=false ./script/deploy.sh

# Skip Terraform (only deploy applications)
SKIP_TERRAFORM=true ./script/deploy.sh

# Specific environment
ENVIRONMENT=staging ./script/deploy.sh
```

### 2. Automated Deployment via Cloud Build

**Push to main branch:**
- Triggers `deploy-backend-main` (builds backend image)
- Triggers `build-workers-main` (builds worker images)

**Create a git tag:**
```bash
git tag v1.0.0
git push origin v1.0.0
```
- Triggers `deploy-tag` (full deployment)

### 3. Individual Component Deployment

**Deploy only infrastructure changes:**
```bash
cd infra/terraform
terraform init
terraform plan -var="project_id=YOUR_PROJECT"
terraform apply
```

**Deploy only workers:**
```bash
# Get cluster credentials
gcloud container clusters get-credentials production-hey-sh-cluster \
  --region europe-west3

# Sync secrets
./infra/k8s/sync-secrets.sh

# Deploy via Helm
helm upgrade --install temporal-workers ./infra/helm/temporal-workers \
  --namespace temporal-workers \
  --create-namespace \
  -f ./infra/helm/temporal-workers/values-production.yaml \
  --set global.projectId=YOUR_PROJECT \
  --set image.repository=YOUR_PROJECT/hey-sh-backend \
  --set image.tag=latest
```

**Deploy only backend API:**
```bash
# Build image
gcloud builds submit --config cloudbuild_backend.yaml

# Update Cloud Run (or let Terraform manage it)
gcloud run services update api \
  --image europe-west3-docker.pkg.dev/YOUR_PROJECT/hey-sh-backend/service:latest \
  --region europe-west3
```

## Environment Variables

Set these before running deployments:

```bash
export ENVIRONMENT=production       # or staging, development
export REGION=europe-west3
export VERSION=$(git rev-parse --short HEAD)
```

## Prerequisites

1. **Install required tools:**
   ```bash
   # Google Cloud SDK
   curl https://sdk.cloud.google.com | bash

   # Terraform
   brew install terraform

   # Helm
   brew install helm

   # kubectl
   gcloud components install kubectl
   ```

2. **Authenticate with GCP:**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   gcloud auth application-default login
   ```

3. **Setup Terraform backend (optional but recommended):**
   ```bash
   # Create GCS bucket for Terraform state
   gsutil mb gs://YOUR_PROJECT-terraform-state

   # Enable versioning
   gsutil versioning set on gs://YOUR_PROJECT-terraform-state
   ```

4. **Create secrets in Secret Manager:**
   ```bash
   # Example: Create a secret
   echo -n "your-secret-value" | gcloud secrets create SECRET_NAME --data-file=-
   ```

## First Time Setup

1. **Initialize Terraform:**
   ```bash
   cd infra/terraform
   terraform init
   ```

2. **Create terraform.tfvars:**
   ```hcl
   project_id  = "your-gcp-project-id"
   region      = "europe-west3"
   environment = "production"
   ```

3. **Apply infrastructure:**
   ```bash
   terraform plan
   terraform apply
   ```

4. **Deploy applications:**
   ```bash
   cd ../..
   ./script/deploy.sh
   ```

## Secrets Management

Secrets are stored in GCP Secret Manager and synced to Kubernetes:

```bash
# Sync secrets to Kubernetes
./infra/k8s/sync-secrets.sh

# Add a new secret
gcloud secrets create NEW_SECRET --data-file=-
echo "secret-value" | gcloud secrets create NEW_SECRET --data-file=-

# Update Terraform to grant access
# Edit infra/terraform/main.tf to add the secret to locals.secrets_to_grant
```

## Monitoring Deployments

**Check Cloud Run:**
```bash
gcloud run services describe api --region europe-west3
```

**Check GKE Pods:**
```bash
kubectl get pods -n temporal-workers
kubectl logs -n temporal-workers -l worker-type=general -f
```

**Check Cloud Build status:**
```bash
gcloud builds list --limit=5
gcloud builds log BUILD_ID
```

## Rollback

**Rollback Cloud Run:**
```bash
gcloud run services update-traffic api \
  --to-revisions REVISION_NAME=100 \
  --region europe-west3
```

**Rollback Helm:**
```bash
helm rollback temporal-workers -n temporal-workers
```

**Rollback Terraform:**
```bash
cd infra/terraform
terraform plan -var="project_id=YOUR_PROJECT"
terraform apply  # After reverting your .tf files
```

## Common Issues

**Issue: Terraform state lock**
```bash
# Force unlock (use with caution)
terraform force-unlock LOCK_ID
```

**Issue: Helm deployment timeout**
```bash
# Increase timeout
helm upgrade --install temporal-workers ./infra/helm/temporal-workers --timeout 20m
```

**Issue: Secrets not syncing**
```bash
# Manually sync secrets
./infra/k8s/sync-secrets.sh

# Check secret exists
gcloud secrets describe SECRET_NAME
```

## Best Practices

1. **Always use Terraform for infrastructure changes** - Don't use `gcloud` commands that modify infrastructure
2. **Use Helm for Kubernetes workloads** - Don't use raw `kubectl apply`
3. **Version your deployments** - Use git tags for production releases
4. **Test in staging first** - Deploy to staging before production
5. **Monitor deployments** - Check logs and metrics after deploying
6. **Keep secrets in Secret Manager** - Never commit secrets to git

## Migration from Old Scripts

The old deployment scripts (`script/deploy_backend.sh`, `script/deploy_worker.sh`) are deprecated.

**Old way (deprecated):**
```bash
./script/deploy_backend.sh  # ❌ Bypasses Terraform
./script/deploy_worker.sh   # ❌ Bypasses Terraform
```

**New way:**
```bash
./script/deploy.sh  # ✅ Uses Terraform + Helm properly
```

## Contact

For deployment issues, contact the platform team or check:
- [Terraform Registry](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Helm Documentation](https://helm.sh/docs/)
- [GKE Autopilot Documentation](https://cloud.google.com/kubernetes-engine/docs/concepts/autopilot-overview)

# Cloud Build Automation Setup

This guide explains how to set up automatic Docker image builds and deployments to GCR (Google Cloud Registry) on commits to the main branch.

## Overview

The automation pipeline includes:
- **Backend API** - FastAPI service
- **AI Worker** - GPU-optimized worker for AI/ML tasks
- **Storage Worker** - I/O-optimized worker for storage operations
- **General Worker** - General-purpose worker

All images are automatically built, tagged with commit hash and `latest`, and pushed to GCR.

## Prerequisites

1. **GCP Project** with Cloud Build enabled
2. **GitHub Repository** connected to Cloud Build
3. **Service Account** with appropriate permissions
4. **Terraform** (>= 1.5)

## Step 1: Connect GitHub Repository to Cloud Build

This must be done manually in the GCP Console:

1. Go to [Cloud Build Repositories](https://console.cloud.google.com/cloud-build/repositories)
2. Click **CONNECT REPOSITORY**
3. Select **GitHub** as the source
4. Authorize Google Cloud Build to access your GitHub account
5. Select your repository: `kpernyer/hey-sh-workflow`
6. Click **CREATE PUSH TRIGGER** to create the initial connection

## Step 2: Configure Terraform Variables

Create or update `terraform/prod/terraform.tfvars`:

```hcl
gcp_project_id            = "hey-sh-production"
gcp_region                = "us-central1"
gcp_zone                  = "us-central1-a"
environment               = "prod"

# Supabase credentials
supabase_url              = "your-supabase-url"
supabase_key              = "your-supabase-key"
supabase_jwt_secret       = "your-jwt-secret"

# Temporal Cloud
temporal_cloud_address    = "your-namespace.temporal.cloud:7233"
temporal_cloud_namespace  = "your-namespace"
temporal_cloud_client_cert = "/path/to/client.crt"
temporal_cloud_client_key = "/path/to/client.key"

# API Keys
openai_api_key            = "your-openai-key"
anthropic_api_key         = "your-anthropic-key"

# Optional: Slack notifications
slack_webhook_url         = "https://hooks.slack.com/services/..."
```

## Step 3: Deploy Cloud Build Trigger with Terraform

```bash
cd terraform/prod

# Initialize Terraform
terraform init

# Plan the deployment
terraform plan

# Apply the configuration (creates Cloud Build trigger)
terraform apply
```

This will create:
- Cloud Build trigger for main branch pushes
- Cloud Build trigger for pull request validation
- GCS bucket for build artifacts
- Appropriate IAM permissions for Cloud Build service account

## Step 4: Verify Setup

1. Push a test commit to the main branch:
```bash
git commit --allow-empty -m "test: trigger cloud build"
git push origin main
```

2. Monitor the build in Cloud Build console:
   - Go to [Cloud Build Dashboard](https://console.cloud.google.com/cloud-build/builds)
   - Watch the build progress
   - Check logs for any failures

## Build Pipeline Details

### Build Steps (in order)

1. **Backend Tests** - Run pytest on backend code
2. **Build Backend API** - Docker build for API service
3. **Build AI Worker** - Docker build for AI worker (GPU-enabled)
4. **Build Storage Worker** - Docker build for storage worker
5. **Build General Worker** - Docker build for general-purpose worker
6. **Push Images to GCR** - Upload all images (tagged with commit hash and `latest`)
7. **Apply Terraform** - Update infrastructure with new image tags
8. **Deploy to GKE** - Update API and workers deployments
9. **Run Smoke Tests** - Validate deployment with basic health checks

### Image Naming Convention

All images follow this pattern:

```
gcr.io/{PROJECT_ID}/hey-sh-{SERVICE_NAME}:{COMMIT_SHORT_SHA}
gcr.io/{PROJECT_ID}/hey-sh-{SERVICE_NAME}:latest
```

Example:
- `gcr.io/hey-sh-production/hey-sh-backend:a1b2c3d`
- `gcr.io/hey-sh-production/hey-sh-backend:latest`
- `gcr.io/hey-sh-production/hey-sh-ai-worker:a1b2c3d`
- `gcr.io/hey-sh-production/hey-sh-general-worker:latest`

## Build Configuration

The build configuration is defined in `cloudbuild.yaml`:

- **Machine Type**: N1_HIGHCPU_8 (8 vCPUs, high CPU for fast builds)
- **Timeout**: 1 hour (3600s)
- **Logging**: Cloud Logging only

## Pull Request Validation

On every pull request to main:
1. Backend tests run
2. All images are built (but not pushed)
3. Code is validated without modifying production

This allows developers to verify builds before merging.

## Manual Build Trigger

To manually trigger a build without pushing code:

```bash
gcloud builds submit \
  --config=cloudbuild.yaml \
  --project=hey-sh-production
```

## Slack Notifications

To enable Slack notifications on build failures:

1. Create a Slack webhook URL in your Slack workspace
2. Update Terraform variables:
```hcl
slack_webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```
3. Re-apply Terraform:
```bash
terraform apply
```

## Troubleshooting

### Build fails with "permission denied"

Cloud Build service account needs permissions:
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com \
  --role roles/container.developer
```

### Images not appearing in GCR

Check Cloud Build logs:
```bash
gcloud builds log BUILD_ID --stream
```

### Terraform apply fails

Ensure:
1. GitHub repository is connected to Cloud Build
2. All required GCP APIs are enabled:
   ```bash
   gcloud services enable \
     cloudbuild.googleapis.com \
     containerregistry.googleapis.com \
     container.googleapis.com \
     run.googleapis.com
   ```

## Monitoring

Monitor builds and deployments:

1. **Cloud Build Dashboard**: https://console.cloud.google.com/cloud-build/builds
2. **Container Registry**: https://console.cloud.google.com/gcr
3. **GKE Workloads**: https://console.cloud.google.com/kubernetes/workloads
4. **Cloud Run Services**: https://console.cloud.google.com/run

## Cost Optimization

- Cloud Build: 120 free build-minutes per day
- GCR Storage: $0.026/GB per month
- Estimated cost: $50-150/month for production builds and storage

To reduce costs:
1. Delete old images (keep only recent 5-10)
2. Adjust build frequency (e.g., only on releases)
3. Use smaller machine types if builds complete quickly

## Next Steps

After successful setup:
1. Configure monitoring and alerting
2. Set up automatic rollback on failed deployments
3. Implement canary deployments for gradual rollouts
4. Add security scanning to build pipeline

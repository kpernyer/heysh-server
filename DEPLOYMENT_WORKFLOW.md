# Deployment Workflow Guide

## 🎯 TL;DR - How You Should Deploy

```bash
# Make your code changes
vim src/...

# Deploy to production (one command!)
just deploy-production v1.2.3 "Add new feature"

# That's it! ☕ Grab coffee while Cloud Build handles everything
```

**You should NEVER need to run:**
- ❌ `terraform apply`
- ❌ `gcloud run deploy`
- ❌ `helm upgrade`
- ❌ `kubectl apply`
- ❌ `docker build/push`

**These are ONLY needed for:**
- Initial infrastructure setup (one-time)
- Infrastructure changes (rare)
- Emergency debugging

---

## 📋 Available Deployment Commands

### Production Deployment

```bash
# Standard production deployment
just deploy-production v1.2.3 "Add user authentication"

# Quick deploy with auto-generated version
just deploy-quick "Hotfix: Fix login bug"
```

### Staging Deployment

```bash
# Deploy to staging environment
just deploy-staging v1.2.3-beta "Test new feature"
```

### Monitoring & Health Checks

```bash
# Check deployment status
just deploy-status

# View logs for a specific build
just deploy-logs <build-id>

# Check if backend is healthy
just deploy-check-health

# Test API endpoints
just deploy-check-api
```

### Rollback

```bash
# Rollback to previous version
just deploy-rollback v1.2.2
```

---

## 🔄 How It Works (Behind the Scenes)

### 1. You Run the Command
```bash
just deploy-production v1.2.3 "Add feature"
```

### 2. Git Operations
```
✅ Stage changes (git add -A)
✅ Create commit
✅ Create version tag (v1.2.3)
✅ Push to GitHub
```

### 3. Cloud Build Trigger Activates
GitHub webhook triggers Cloud Build when it sees tag matching `v*`

### 4. Cloud Build Pipeline (`cloudbuild_deploy.yaml`)
```
Step 1: Build backend Docker image       [~30s]
Step 2: Build general worker image       [~40s]
Step 3: Build AI worker image            [~40s]
Step 4: Build storage worker image       [~40s]
Step 5: Push backend image               [~10s]
Step 6: Push general worker image        [~10s]
Step 7: Push AI worker image             [~10s]
Step 8: Push storage worker image        [~10s]
Step 9: Deploy backend to Cloud Run      [~60s]
Step 10: Deploy workers to GKE via Helm  [~180s]
```

### 5. Result
```
✅ Backend API live at: https://api-blwol5d45q-ey.a.run.app
✅ Workers running on GKE cluster
✅ All services healthy
```

**Total time: 5-10 minutes**

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         GitHub                              │
│  ┌──────────────┐     Push Tag      ┌──────────────┐      │
│  │ Local Repo   │ ────────────────> │ Remote Repo  │      │
│  └──────────────┘                   └──────┬───────┘      │
└──────────────────────────────────────────────┼──────────────┘
                                              │
                                    Webhook   │
                                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Google Cloud Build                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  cloudbuild_deploy.yaml                              │  │
│  │  - Build images                                      │  │
│  │  - Push to Artifact Registry                         │  │
│  │  - Deploy backend                                    │  │
│  │  - Deploy workers                                    │  │
│  └───────┬──────────────────────────────────┬───────────┘  │
└──────────┼──────────────────────────────────┼──────────────┘
           │                                  │
           ▼                                  ▼
┌────────────────────────┐      ┌────────────────────────────┐
│   Cloud Run (Backend)  │      │  GKE Cluster (Workers)     │
│  ┌──────────────────┐  │      │  ┌──────────────────────┐ │
│  │  API Service     │  │      │  │  General Worker      │ │
│  │  (Autoscaling)   │  │      │  │  AI Worker (GPU)     │ │
│  └──────────────────┘  │      │  │  Storage Worker      │ │
└────────────────────────┘      │  └──────────────────────┘ │
                                └────────────────────────────┘
```

---

## 🔧 Setting Up Staging Environment

Currently, you have **production only**. Here's how to add staging:

### Option 1: Separate GCP Project (Recommended)

**Pros:** Complete isolation, separate billing, true production replica
**Cons:** Higher cost

```bash
# 1. Create new GCP project
gcloud projects create hey-sh-staging

# 2. Set up infrastructure
cd infra/terraform
terraform workspace new staging
terraform apply -var="project_id=hey-sh-staging" -var="environment=staging"

# 3. Create Cloud Build trigger for staging tags
gcloud builds triggers create github \
  --repo-name=heysh-server \
  --repo-owner=kpernyer \
  --branch-pattern="^main$" \
  --tag-pattern="^staging-.*" \
  --build-config=cloudbuild_deploy.yaml \
  --substitutions=_DEPLOY_ENV=staging

# 4. Deploy to staging
just deploy-staging v1.2.3-beta "Test feature"
```

### Option 2: Same Project, Different Namespace (Cheaper)

**Pros:** Lower cost, easier to manage
**Cons:** Shared resources, not true isolation

```bash
# 1. Create staging Cloud Run service
gcloud run services create api-staging \
  --image=europe-west3-docker.pkg.dev/hey-sh-production/hey-sh-backend/service:latest \
  --region=europe-west3 \
  --platform=managed

# 2. Create staging Cloud Build trigger
gcloud builds triggers create github \
  --repo-name=heysh-server \
  --repo-owner=kpernyer \
  --branch-pattern="^main$" \
  --tag-pattern="^staging-.*" \
  --build-config=cloudbuild_staging.yaml

# 3. Create cloudbuild_staging.yaml with different service name
# (Similar to cloudbuild_deploy.yaml but deploys to api-staging)

# 4. Deploy workers to staging namespace
kubectl create namespace temporal-workers-staging
```

### Option 3: Branch-based Deployment (Simplest)

**Pros:** Simplest, automatic
**Cons:** Less control, harder to version

```bash
# 1. Create staging branch
git checkout -b staging

# 2. Create Cloud Build trigger for staging branch
gcloud builds triggers create github \
  --repo-name=heysh-server \
  --repo-owner=kpernyer \
  --branch-pattern="^staging$" \
  --build-config=cloudbuild_deploy.yaml \
  --substitutions=_DEPLOY_ENV=staging

# 3. Deploy to staging
git push origin staging

# 4. Promote to production
git checkout main
git merge staging
just deploy-production v1.2.3 "Release"
```

---

## 📊 Current Cloud Build Triggers

You currently have **3 triggers** configured:

| Trigger Name | File | Trigger | Environment | Purpose |
|--------------|------|---------|-------------|---------|
| `deploy-tag` | `cloudbuild_deploy.yaml` | Tag: `v*` | Production | Full deployment (backend + workers) |
| `deploy-backend-main` | `cloudbuild_backend.yaml` | Branch: `main` | Development | Backend only |
| `build-workers-main` | `cloudbuild_workers.yaml` | Branch: `main` | Development | Workers only |

**Recommendation:** You only need `deploy-tag` for production. The other two can be removed or disabled.

---

## 🚀 Typical Workflow Examples

### Example 1: Feature Development
```bash
# 1. Develop locally
just dev
# ... make changes ...
just test

# 2. Commit & push (no deployment yet)
git add .
git commit -m "WIP: New feature"
git push

# 3. When ready for production
just deploy-production v1.3.0 "Add search functionality"

# 4. Monitor deployment
just deploy-status

# 5. Verify it's working
just deploy-check-health
just deploy-check-api
```

### Example 2: Hotfix
```bash
# 1. Fix the bug
vim src/service/routes.py

# 2. Quick deploy with auto-version
just deploy-quick "Hotfix: Fix authentication bug"

# 3. Monitor
just deploy-status
```

### Example 3: Staging → Production
```bash
# 1. Deploy to staging first
just deploy-staging v1.4.0-beta "Test new billing feature"

# 2. Test on staging
curl https://api-staging-blwol5d45q-ey.a.run.app/health

# 3. If good, deploy to production
just deploy-production v1.4.0 "Add billing feature"
```

### Example 4: Something Broke - Rollback
```bash
# 1. Check current status
just deploy-status

# 2. Rollback to last known good version
just deploy-rollback v1.3.5

# 3. Verify
just deploy-check-health
```

---

## 📈 Monitoring Deployments

### Check Status
```bash
# See last 5 deployments
just deploy-status

# Output:
# ID            STATUS    CREATE_TIME       TAG      LOG_URL
# abc123...     SUCCESS   2025-01-28 10:30  v1.2.3   https://...
# def456...     WORKING   2025-01-28 10:25  v1.2.2   https://...
```

### View Logs
```bash
# Get build ID from deploy-status, then:
just deploy-logs abc123...

# Or view in browser (Cloud Console)
open https://console.cloud.google.com/cloud-build/builds
```

### Check Health
```bash
# Backend health
just deploy-check-health

# API endpoints
just deploy-check-api
```

---

## 🛡️ When You WOULD Need Manual Commands

### 1. Initial Setup (One-time)
```bash
# Set up GCP project
gcloud projects create hey-sh-production

# Deploy infrastructure
cd infra/terraform
terraform init
terraform apply
```

### 2. Infrastructure Changes (Rare)
```bash
# Adding new GCP service (e.g., Cloud Storage bucket)
cd infra/terraform
vim main.tf  # Add new resource
terraform plan
terraform apply
```

### 3. Debugging Deployments
```bash
# Check Cloud Run logs
gcloud run logs read api --region=europe-west3 --limit=100

# Check worker pods
kubectl get pods -n temporal-workers
kubectl logs -n temporal-workers <pod-name>

# Check images in registry
gcloud artifacts docker images list \
  europe-west3-docker.pkg.dev/hey-sh-production/hey-sh-backend
```

### 4. Emergency Manual Deployment
```bash
# If Cloud Build is down, manually deploy
gcloud run services update api \
  --image=europe-west3-docker.pkg.dev/hey-sh-production/hey-sh-backend/service:v1.2.3 \
  --region=europe-west3
```

---

## 🎓 Best Practices

### 1. Semantic Versioning
```bash
# Major version (breaking changes)
just deploy-production v2.0.0 "Major refactor: New API"

# Minor version (new features)
just deploy-production v1.3.0 "Add user profiles"

# Patch version (bug fixes)
just deploy-production v1.2.1 "Fix login bug"
```

### 2. Descriptive Messages
```bash
# ✅ Good
just deploy-production v1.2.3 "Add password reset functionality"

# ❌ Bad
just deploy-production v1.2.3 "updates"
```

### 3. Test Before Production
```bash
# Always test locally first
just dev
just test
just test-api

# Then deploy to staging (if available)
just deploy-staging v1.2.3-beta "Test feature"

# Finally production
just deploy-production v1.2.3 "Release feature"
```

### 4. Monitor After Deployment
```bash
# Deploy
just deploy-production v1.2.3 "Update auth"

# Monitor (wait 5-10 minutes)
just deploy-status

# Verify
just deploy-check-health
just deploy-check-api

# Check logs if issues
just deploy-logs <build-id>
```

---

## 🔍 Troubleshooting

### Deployment Failed
```bash
# 1. Check status
just deploy-status

# 2. View logs
just deploy-logs <failed-build-id>

# 3. Common issues:
#    - Docker build failed → Check Dockerfile syntax
#    - Tests failed → Run `just test` locally
#    - Image not found → Check cloudbuild_deploy.yaml
#    - Helm timeout → Check GKE cluster capacity
```

### Backend Not Responding
```bash
# 1. Check health
just deploy-check-health

# 2. Check Cloud Run logs
gcloud run logs read api --region=europe-west3 --limit=100

# 3. Check Cloud Run status
gcloud run services describe api --region=europe-west3
```

### Workers Not Processing
```bash
# 1. Check worker pods
kubectl get pods -n temporal-workers

# 2. Check worker logs
kubectl logs -n temporal-workers -l worker-type=general -f

# 3. Check Temporal UI
open https://cloud.temporal.io
```

---

## 📚 Additional Resources

- **Cloud Build Docs**: https://cloud.google.com/build/docs
- **Cloud Run Docs**: https://cloud.google.com/run/docs
- **GKE Docs**: https://cloud.google.com/kubernetes-engine/docs
- **Helm Docs**: https://helm.sh/docs/

---

## 🎯 Summary

**Your workflow should be:**
```bash
# 1. Make changes
vim src/...

# 2. Test locally
just dev
just test

# 3. Deploy
just deploy-production v1.2.3 "Description"

# 4. Monitor
just deploy-status

# 5. Verify
just deploy-check-health
```

**That's it! No terraform, no gcloud, no kubectl needed for normal deployments.**

---

**Last Updated:** 2025-01-29
**Author:** Claude Code
**Status:** ✅ Production Ready

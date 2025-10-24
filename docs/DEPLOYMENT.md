# Hey.sh Production Deployment Guide

Complete guide for deploying Hey.sh to production using Terraform and Cloud Build.

## 📋 What's Included

### 1. Local Development Environment
**File**: `docker-compose.yml`

Complete local development stack with all services:
- API Server (FastAPI)
- Temporal Workflow Engine
- 3-Tier Worker Queues:
  - AI Processing (GPU-enabled)
  - Storage (I/O optimized)
  - General (lightweight)
- PostgreSQL (Temporal state)
- Neo4j (Graph database)
- Weaviate (Vector search)

**Quick Start**:
```bash
docker-compose up
pnpm dev  # In another terminal
open http://temporal.hey.local  # Temporal UI
```

### 2. Production Infrastructure as Code
**Directory**: `terraform/prod/`

Complete Terraform configuration for GCP deployment:
- **main.tf**: Infrastructure definitions
- **variables.tf**: 40+ configurable parameters
- **terraform.tfvars.example**: Example values

**Deployment Resources**:
- API Server (Cloud Run, 3 replicas, auto-scaling)
- AI Workers (GKE, 1 replica with GPU)
- Storage Workers (GKE, 2 replicas, I/O optimized)
- General Workers (GKE, 3 replicas)
- Networking (VPC, private subnets)

**Deploy**:
```bash
cd terraform/prod
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

### 3. Automated CI/CD Pipeline
**File**: `cloudbuild.yaml`

Complete Google Cloud Build pipeline:
1. Test backend code
2. Build Docker images (API + 3 worker types)
3. Push to Google Container Registry (GCR)
4. Apply Terraform infrastructure
5. Deploy to Cloud Run / GKE
6. Run smoke tests
7. Slack notifications on success/failure

**Triggers automatically on git push to main**.

### 4. 3-Tier Worker Queue Configuration
**File**: `docs/WORKERS.md`

Comprehensive worker queue documentation:
- **AI Processing Queue**: 16GB RAM, 4 CPU, GPU (Tesla T4)
  - LLM inference, document analysis, NLP tasks
  - 1 replica, 5 concurrent activities

- **Storage Queue**: 8GB RAM, 2 CPU
  - Database operations, indexing, I/O intensive
  - 2 replicas, 20 concurrent activities

- **General Queue**: 4GB RAM, 1 CPU
  - Coordination, validation, management
  - 3 replicas, 50 concurrent activities

**Task Routing Example**:
```python
await client.execute_workflow(
    "DocumentProcessingWorkflow",
    args=[document_id],
    task_queue="storage-queue"  # Routes to storage workers
)
```

## 🎯 Deployment Checklist

### Pre-Deployment

- [ ] All code pushed to `main` branch
- [ ] Tests passing locally (`just test`)
- [ ] Linting passing (`just lint`)
- [ ] Environment variables defined in `.env.example`
- [ ] GCP project created and configured
- [ ] Service account with appropriate permissions created
- [ ] Billing enabled on GCP project

### Initial Setup (One-time)

```bash
# 1. Create Terraform variables file
cp terraform/prod/terraform.tfvars.example terraform/prod/terraform.tfvars

# 2. Edit with your GCP project details
vim terraform/prod/terraform.tfvars
# Fill in:
# - gcp_project_id
# - gcp_region
# - All Supabase credentials
# - API keys (OpenAI, Anthropic)
# - Temporal Cloud credentials

# 3. Initialize Terraform
cd terraform/prod
terraform init

# 4. Verify plan (no changes, just preview)
terraform plan -var-file=terraform.tfvars
```

### Deploy Infrastructure

```bash
# 1. Apply Terraform (creates all GCP resources)
terraform apply -var-file=terraform.tfvars

# 2. Wait for completion (5-15 minutes)
# - GKE cluster provisioning
# - Cloud Run service creation
# - Network configuration

# 3. Verify deployment
gcloud run services list
kubectl get nodes
tctl namespace list
```

### Setup CI/CD Pipeline

```bash
# 1. Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable run.googleapis.com

# 2. Connect GitHub repository
gcloud builds connect github \
  --repository-name=hey-sh-workflow \
  --repository-owner=kpernyer \
  --branch-pattern="^main$"

# 3. Submit build configuration
gcloud builds submit --config cloudbuild.yaml

# 4. Verify trigger created
gcloud builds triggers list
```

### Configure Secrets

```bash
# Store all secrets in GCP Secret Manager
gcloud secrets create SUPABASE_URL --data-file=- <<< "https://your-project.supabase.co"
gcloud secrets create SUPABASE_KEY --data-file=- <<< "your_anon_key"
gcloud secrets create SUPABASE_JWT_SECRET --data-file=- <<< "your_jwt_secret"
gcloud secrets create OPENAI_API_KEY --data-file=- <<< "sk-..."
gcloud secrets create ANTHROPIC_API_KEY --data-file=- <<< "sk-..."

# Verify secrets created
gcloud secrets list
```

## 🚀 Deployment Workflow

### For Local Development

1. **Copy environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Add Supabase credentials** to `.env`:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your_key
   SUPABASE_JWT_SECRET=your_secret
   ```

3. **Start services**:
   ```bash
   docker-compose up
   ```

4. **In another terminal, start frontend**:
   ```bash
   pnpm dev
   ```

5. **Access services**:
   - API: http://api.hey.local
   - Temporal UI: http://temporal.hey.local
   - Weaviate: http://weaviate.hey.local
   - Frontend: http://hey.local

### For Production Deployment

1. **Prepare Terraform variables**:
   ```bash
   cp terraform/prod/terraform.tfvars.example terraform/prod/terraform.tfvars
   ```

2. **Fill in values**:
   ```bash
   vim terraform/prod/terraform.tfvars
   # Edit: GCP project, Supabase credentials, API keys, etc.
   ```

3. **Deploy infrastructure**:
   ```bash
   cd terraform/prod
   terraform init
   terraform plan -var-file=terraform.tfvars
   terraform apply -var-file=terraform.tfvars
   ```

4. **Set up Cloud Build**:
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```

5. **Push to main** (auto-deploys via Cloud Build):
   ```bash
   git push origin main
   ```

## 📊 Architecture Overview

```
┌─────────────────────────────────────┐
│    Frontend (Lovable)               │
│  React + TypeScript + Supabase      │
└────────────┬────────────────────────┘
             │ REST API
             ▼
┌─────────────────────────────────────┐
│    API Server (FastAPI)             │
│  Cloud Run (serverless)             │
└────────────┬────────────────────────┘
             │
     ┌───────┼───────┐
     ▼       ▼       ▼
┌────────┐ ┌──────────────┐ ┌──────────┐
│Supabase│ │ Temporal     │ │Databases │
│        │ │ Cloud        │ │          │
│- Auth  │ │ - Workflows  │ │- Neo4j   │
│- Files │ │ - 3 Queues   │ │- Weaviate│
│- DB    │ │ - Workers    │ │- Postgres│
└────────┘ └──────────────┘ └──────────┘
```

**3-Tier Workers** (on GKE):
- AI Processing (GPU-enabled) → 1 instance
- Storage (I/O optimized) → 2 instances
- General (lightweight) → 3 instances

## 🔧 Project Structure

```
hey-sh-workflow/
├── docker-compose.yml              # Local dev environment
├── .env.example                    # Environment variables template
├── cloudbuild.yaml                 # CI/CD pipeline
├── docs/
│   ├── DEVELOPMENT.md             # Local setup guide
│   ├── INFRASTRUCTURE.md          # Architecture docs
│   ├── WORKERS.md                 # Queue configuration
│   └── DEPLOYMENT.md              # This file
├── backend/
│   ├── Dockerfile                 # API server image
│   ├── deployments/
│   │   ├── Dockerfile.ai-worker   # AI worker image
│   │   └── Dockerfile.storage-worker # Storage worker image
│   └── worker/
│       └── multiqueue_worker.py    # Worker implementations
└── terraform/
    └── prod/
        ├── main.tf               # Infrastructure
        ├── variables.tf          # Configuration
        └── terraform.tfvars.example # Example values
```

## ✨ Key Features

✅ **Production-Ready Infrastructure**
- Auto-scaling workers (1-10 instances)
- Managed databases (Aura, Cloud SQL, Weaviate Cloud)
- VPC networking & security

✅ **3-Tier Worker Architecture**
- GPU-enabled AI workers
- I/O optimized storage workers
- Lightweight general workers

✅ **Automated CI/CD**
- Tests → Build → Push → Deploy
- Terraform Infrastructure as Code
- Smoke tests & notifications

✅ **Complete Documentation**
- Local development guide
- Deployment instructions
- Troubleshooting guides
- Architecture diagrams

✅ **Security**
- GCP Secret Manager for credentials
- Private GKE cluster
- VPC networking
- Supabase JWT authentication

✅ **Cost Optimization**
- Auto-scaling based on queue depth
- Serverless API (Cloud Run)
- Resource limits per worker type

## 🔐 Security Checklist

- [ ] Supabase credentials in `.env` (not committed)
- [ ] GCP credentials configured
- [ ] Secrets in GCP Secret Manager
- [ ] Private GKE cluster configured
- [ ] VPC network isolation enabled
- [ ] Cloud Armor enabled for DDoS
- [ ] Audit logging configured
- [ ] Regular backups enabled

## 💬 Quick Reference

### Common Commands

```bash
# Local development
docker-compose up              # Start all services
docker-compose logs -f api     # View API logs
docker-compose down -v         # Clean everything

# Production (Terraform)
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
terraform destroy             # Tear down (careful!)

# Monitoring
gcloud run logs read hey-sh-backend --follow
kubectl logs -f deployment/storage-worker
tctl task-queue describe -task-queue storage-queue
```

### Useful Ports (Local)

- API: 8000 (http://api.hey.local)
- Temporal: 7233
- Temporal UI: 8080 (http://temporal.hey.local)
- Weaviate: 8090 (http://weaviate.hey.local)
- Neo4j: 7687 (http://neo4j.hey.local)
- PostgreSQL: 5432
- Frontend: 5173 (http://hey.local)

## 🚀 Next Steps

### Immediate (Today)
- [ ] Copy `.env.example` to `.env`
- [ ] Add Supabase credentials
- [ ] Run `docker-compose up`
- [ ] Test workflows in Temporal UI

### Short-term (This Week)
- [ ] Set up GCP Secret Manager
- [ ] Create `terraform/prod/terraform.tfvars`
- [ ] Run `terraform plan` to verify
- [ ] Set up Cloud Build triggers

### Medium-term (This Month)
- [ ] Deploy to staging
- [ ] Run load tests
- [ ] Optimize worker queue settings
- [ ] Set up monitoring alerts

### Long-term (Ongoing)
- [ ] Monitor production metrics
- [ ] Optimize costs
- [ ] Scale based on usage
- [ ] Regular security audits

## 📞 Support

- **Setup Issues**: Check [DEVELOPMENT.md](./DEVELOPMENT.md)
- **Architecture Questions**: See [INFRASTRUCTURE.md](./INFRASTRUCTURE.md)
- **Worker Configuration**: Review [WORKERS.md](./WORKERS.md)
- **Troubleshooting**: Check relevant documentation files

---

**Last Updated**: October 21, 2025
**Status**: PRODUCTION READY ✅
**Version**: 1.0

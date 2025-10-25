# Hey.sh Infrastructure Documentation

Complete overview of Hey.sh infrastructure, deployment, and operations.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Lovable)                       │
│                    React + TypeScript + Supabase                 │
└──────────────────┬──────────────────────────────────────────────┘
                   │ REST API Calls
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Server (FastAPI)                        │
│              Routes: /auth, /api/v1/*, /graphql                 │
│   (Runs as Cloud Run service or Kubernetes deployment)          │
└──────────────────┬──────────────────────────────────────────────┘
                   │
    ┌──────────────┼──────────────────┐
    ▼              ▼                   ▼
┌─────────┐  ┌──────────────┐  ┌─────────────┐
│Supabase │  │ Temporal     │  │ Databases   │
│         │  │ Cloud        │  │             │
│- Auth   │  │              │  │- PostgreSQL │
│- Storage│  │- Workflows   │  │- Neo4j      │
│- DB     │  │- Task Queues │  │- Weaviate   │
└─────────┘  └──────────────┘  └─────────────┘
                   │
    ┌──────────────┼──────────────────┐
    ▼              ▼                   ▼
┌──────────────────────────────────────────────────┐
│        3-Tier Worker Queue System                 │
├──────────────────────────────────────────────────┤
│ AI Processing  │  Storage Queue  │  General Queue│
│ (GPU enabled)  │  (I/O optimized)│  (Lightweight)│
│                │                 │               │
│ 1 replica      │  2 replicas     │  3 replicas   │
│ 16GB RAM       │  8GB RAM        │  4GB RAM      │
│ 4 CPU cores    │  2 CPU cores    │  1 CPU core   │
└──────────────────────────────────────────────────┘
```

## Technology Stack

### Frontend
- **Framework**: React 18 with TypeScript
- **UI**: Shadcn/ui components
- **Build**: Vite
- **Auth**: Supabase
- **Storage**: Supabase Storage
- **Deployment**: Lovable (managed)

### Backend API
- **Framework**: FastAPI
- **Server**: Uvicorn
- **Python**: 3.12
- **Authentication**: JWT (Supabase)
- **Deployment**: Cloud Run (serverless) or GKE

### Workflow Engine
- **Platform**: Temporal Cloud
- **Task Queues**: 3-tier specialized queues
- **Workers**: Kubernetes deployments or Compute Engine VMs

### Databases
- **Temporal State**: PostgreSQL (Cloud SQL)
- **Graph Data**: Neo4j Aura
- **Vector Search**: Weaviate Cloud
- **User Data**: Supabase (PostgreSQL)

## Local Development

### Start Complete Environment

```bash
# All services (API, Temporal, Workers, Databases)
docker-compose up

# Frontend (separate terminal)
pnpm dev
```

### Services

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| API | 8000 | http://localhost:8000 | REST API server |
| Temporal | 7233 | http://localhost:7233 | Workflow engine |
| Temporal UI | 8080 | http://localhost:8080 | Workflow monitoring |
| Weaviate | 8090 | http://localhost:8090 | Vector search |
| Neo4j | 7687 | bolt://localhost:7687 | Graph database |
| PostgreSQL | 5432 | localhost:5432 | Temporal database |

See [DEVELOPMENT.md](./DEVELOPMENT.md) for detailed guide.

## Production Deployment

### Infrastructure as Code

All production infrastructure is managed with Terraform:

```bash
cd terraform/prod

# Plan infrastructure changes
terraform plan -var-file=terraform.tfvars

# Apply changes
terraform apply -var-file=terraform.tfvars
```

### Deployment Topology

**API Server**:
- Cloud Run (serverless) - auto-scales 0-10 instances
- 2Gi memory, 2 CPU per instance
- 3 minimum replicas

**Workers**:
- GKE (Kubernetes cluster)
- AI Processing: 1 replica with GPU (Tesla T4)
- Storage: 2 replicas (horizontal scaling)
- General: 3 replicas (horizontal scaling)

**Databases**:
- PostgreSQL: Cloud SQL (managed)
- Neo4j: Neo4j Aura (managed)
- Weaviate: Weaviate Cloud (managed)
- Supabase: Managed hosting

### Environment Variables

Store all secrets in GCP Secret Manager:

```bash
# API secrets
gcloud secrets create SUPABASE_URL --data-file=- <<< "https://..."
gcloud secrets create SUPABASE_KEY --data-file=- <<< "sk-..."

# Worker secrets
gcloud secrets create OPENAI_API_KEY --data-file=- <<< "sk-..."
```

### Networking

```bash
# VPC and subnets
terraform apply # creates private GKE cluster on private VPC
```

## CI/CD Pipeline

### Cloud Build Configuration

Automated deployment on every push to main:

1. **Build** - Docker images for API and workers
2. **Test** - Run pytest and linting
3. **Push** - Push images to GCR
4. **Deploy** - Apply Terraform and deploy services
5. **Test** - Run smoke tests
6. **Notify** - Slack notification on success/failure

See [../cloudbuild.yaml](../cloudbuild.yaml) for details.

### Manual Deployment

```bash
# Build images
docker build -t gcr.io/hey-sh-production/hey-sh-backend:latest backend/

# Push to GCR
docker push gcr.io/hey-sh-production/hey-sh-backend:latest

# Deploy with Terraform
cd terraform/prod
terraform apply -var-file=terraform.tfvars
```

## 3-Tier Worker Architecture

### Queue Distribution

| Queue | Task Type | CPU | Memory | GPU | Scaling |
|-------|-----------|-----|--------|-----|---------|
| ai-processing-queue | AI inference, NLP, LLM | 4 | 16GB | 1x T4 | 1-2 |
| storage-queue | Database, indexing, I/O | 2 | 8GB | - | 2-4 |
| general-queue | Coordination, validation | 1 | 4GB | - | 3-5 |

### Task Routing

```python
# Each workflow specifies target queue
await client.execute_workflow(
    "DocumentProcessingWorkflow",
    args=[...],
    task_queue="storage-queue"  # Explicit queue selection
)
```

See [WORKERS.md](./WORKERS.md) for detailed configuration.

## Monitoring & Logging

### Logs

```bash
# API logs
gcloud run logs read hey-sh-backend --region us-central1 --follow

# Worker logs
kubectl logs -f deployment/ai-worker
kubectl logs -f deployment/storage-worker

# Temporal logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=hey-sh-backend"
```

### Metrics

```bash
# Cloud Monitoring dashboards
# - API response time
# - Worker queue depth
# - Task completion rate
# - Error rates by queue
```

## Troubleshooting

### Service Won't Start

```bash
# Check API logs
gcloud run logs read hey-sh-backend --region us-central1

# Check worker connectivity to Temporal
kubectl logs -f deployment/storage-worker | grep -i temporal

# Verify environment variables
kubectl describe deployment storage-worker
```

### Slow Task Execution

```bash
# Check queue backlog
tctl task-queue describe -task-queue storage-queue

# Add more replicas
kubectl scale deployment storage-worker --replicas=5

# Check resource utilization
kubectl top pod | grep worker
```

### Database Connection Issues

```bash
# Check Cloud SQL instance status
gcloud sql instances describe hey-sh-db

# Verify network connectivity
gcloud compute ssh worker-vm --zone us-central1-a -- nc -zv cloudsql-proxy:3306
```

## Scaling

### Horizontal Scaling

```bash
# Increase worker replicas
kubectl scale deployment storage-worker --replicas=10

# Or use HPA (Horizontal Pod Autoscaler)
kubectl autoscale deployment storage-worker --min=2 --max=10
```

### Vertical Scaling

```bash
# Increase memory/CPU in docker-compose
# Edit docker-compose.yml:
# - memory: 16Gi → 32Gi
# - cpus: '4' → '8'

# Or in Terraform:
# - memory = "16Gi" → "32Gi"
```

## Disaster Recovery

### Backup Strategy

```bash
# Automated Cloud SQL backups (daily)
gcloud sql backups create --instance=hey-sh-db

# Temporal state in PostgreSQL (managed)
# Neo4j backups (via Aura)
```

### Recovery Procedures

```bash
# Restore from backup
gcloud sql backups restore BACKUP_ID --backup-instance=hey-sh-db --backup-configuration=default

# Redeploy services
terraform apply
```

## Security

### Secrets Management

All secrets stored in GCP Secret Manager:

```bash
# Rotate API keys
gcloud secrets versions add SUPABASE_KEY --data-file=-

# Audit secret access
gcloud logging read "resource.type=secretmanager.googleapis.com"
```

### Network Security

- Private GKE cluster (no public IP)
- VPC with private subnets
- Cloud SQL Proxy for database access
- Cloud Armor for DDoS protection

### Authentication

- Supabase JWT for user auth
- Temporal mTLS for Cloud
- GCP IAM for infrastructure

## Cost Optimization

### Resource Allocation

- Use `n1-standard` for general workers
- Use `n1-highmem` for storage workers
- Use `n1-highcpu` for AI workers with GPU

### Auto-scaling

```hcl
# Terraform configuration for cost optimization
resource "google_compute_autoscaler" "storage_workers" {
  min_node_count = 2      # Cost baseline
  max_node_count = 10     # Scale on demand
  target_cpu_utilization = 0.7  # Efficient scaling
}
```

### Quotas & Limits

```bash
# View current usage
gcloud compute project-info describe --project=hey-sh-production

# Set spending alerts
gcloud billing budgets create ...
```

## Runbooks

### Deploying New Feature

1. Create feature branch
2. Push to GitHub
3. Cloud Build triggers automatically
4. Monitor deployment in Cloud Console
5. Verify with smoke tests
6. Merge to main on success

### Emergency Rollback

```bash
# Rollback to previous image
gcloud run deploy hey-sh-backend \
  --image gcr.io/hey-sh-production/hey-sh-backend:PREVIOUS_SHA

# Or via Terraform
terraform apply -var-file=previous.tfvars
```

### Scale Up for Load

```bash
# Temporary scale up
kubectl scale deployment general-worker --replicas=20

# Persistent scale up
# Edit Terraform and apply
```

## Contact & Support

- **Platform**: GCP (hey-sh-production)
- **Terraform State**: GCS (hey-sh-terraform-state)
- **Monitoring**: Cloud Monitoring dashboards
- **Alerts**: Slack notifications

---

**Last Updated**: October 21, 2025
**Maintained By**: Platform Team
**Version**: 1.0

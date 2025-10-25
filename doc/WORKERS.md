# Hey.sh 3-Tier Temporal Worker Queue Configuration

## Overview

Hey.sh uses a 3-tier worker queue architecture to optimize task execution based on workload characteristics:

1. **AI Processing Queue** - GPU-intensive ML tasks
2. **Storage Queue** - I/O intensive database and storage operations
3. **General Queue** - Lightweight coordination and management tasks

## Queue Specifications

### 1. AI Processing Queue

**Purpose**: Handle AI model inference, document analysis, and NLP tasks

**Task Queue Name**: `ai-processing-queue`

**Resource Requirements**:
- **CPU**: 4 cores minimum
- **Memory**: 16GB minimum
- **GPU**: NVIDIA Tesla T4 or equivalent
- **Storage**: 50GB SSD

**Concurrency Limits**:
- Max concurrent activities: 5
- Max concurrent workflow tasks: 10

**Suitable For**:
- OpenAI API calls for embeddings
- Document text extraction and analysis
- LLM-powered summarization
- Image processing

**Deployment**:
```bash
# Local
docker-compose up ai-worker

# Production (GCP)
terraform apply -var-file=prod/terraform.tfvars
```

**Example Workflow Tasks**:
```python
@activity
async def analyze_document(document_id: str) -> dict:
    """AI-powered document analysis"""
    # Calls OpenAI API for embeddings and analysis
    pass

@activity
async def generate_summary(content: str) -> str:
    """Generate AI summary using LLM"""
    # Uses Claude or GPT-4
    pass
```

---

### 2. Storage Queue

**Purpose**: Handle database operations, file storage, and vector indexing

**Task Queue Name**: `storage-queue`

**Resource Requirements**:
- **CPU**: 2 cores minimum
- **Memory**: 8GB minimum
- **Storage**: 200GB fast SSD (NVMe preferred)
- **Network**: High throughput to databases

**Concurrency Limits**:
- Max concurrent activities: 20
- Max concurrent workflow tasks: 20

**Suitable For**:
- PostgreSQL/Supabase operations
- Neo4j graph updates
- Weaviate vector indexing
- Document upload/download
- Cache management

**Deployment**:
```bash
# Local (with persistent volume)
docker-compose up storage-worker

# Production
terraform apply -var-file=prod/terraform.tfvars
# Auto-scales to 2 replicas for high availability
```

**Example Workflow Tasks**:
```python
@activity
async def index_document_vectors(document_id: str, vectors: list) -> None:
    """Store vectors in Weaviate and update Neo4j graph"""
    # High volume I/O operations
    pass

@activity
async def sync_database(updates: dict) -> None:
    """Sync multiple database operations"""
    # PostgreSQL + Neo4j transactions
    pass
```

---

### 3. General Queue

**Purpose**: Lightweight coordination, validation, and management tasks

**Task Queue Name**: `general-queue`

**Resource Requirements**:
- **CPU**: 0.5 core minimum
- **Memory**: 4GB minimum
- **Storage**: 20GB standard SSD

**Concurrency Limits**:
- Max concurrent activities: 50
- Max concurrent workflow tasks: 50

**Suitable For**:
- API request routing
- Workflow state management
- Email notifications
- Validation logic
- Logging and monitoring
- User-facing coordination tasks

**Deployment**:
```bash
# Local
docker-compose up general-worker

# Production
terraform apply -var-file=prod/terraform.tfvars
# Auto-scales to 3 replicas for reliability
```

**Example Workflow Tasks**:
```python
@activity
async def validate_document(document_id: str) -> bool:
    """Lightweight validation check"""
    pass

@activity
async def notify_user(user_id: str, message: str) -> None:
    """Send notification to user"""
    pass
```

---

## Task Queue Routing

### How Workflows Choose Queues

```python
from temporalio.worker import Worker

# Each worker subscribes to specific queues
async def create_workers(client: Client):
    # AI Worker
    ai_worker = Worker(
        client,
        task_queue="ai-processing-queue",
        workflows=[...],
        activities=[analyze_document, generate_summary]
    )

    # Storage Worker
    storage_worker = Worker(
        client,
        task_queue="storage-queue",
        workflows=[...],
        activities=[index_vectors, sync_database]
    )

    # General Worker
    general_worker = Worker(
        client,
        task_queue="general-queue",
        workflows=[...],
        activities=[validate, notify]
    )
```

### Workflow Execution

```python
@activity
async def start_document_workflow(document_id: str):
    """Start workflow targeting specific queue"""
    # Route to storage queue for document processing
    await client.execute_workflow(
        "DocumentProcessingWorkflow",
        args=[document_id],
        id=f"doc-{document_id}",
        task_queue="storage-queue"  # ← Explicit queue selection
    )
```

---

## Performance Tuning

### Queue Capacity Planning

| Queue | Expected RPS | Concurrent Tasks | Recommended Replicas |
|-------|---------|----------|------------|
| AI Processing | 1-5 | 5 | 1-2 |
| Storage | 10-50 | 20 | 2-4 |
| General | 50-200 | 50 | 3-5 |

### Monitoring Queue Health

```bash
# Check queue backlog
tctl task-queue describe -task-queue ai-processing-queue

# View queue stats
tctl task-queue stats -task-queue storage-queue

# Monitor worker capacity
kubectl get pods -l app=temporal-worker
```

### Auto-scaling Configuration

```hcl
# In Terraform
resource "google_container_autoscaler" "storage_workers" {
  min_node_count = 2
  max_node_count = 10
  target_cpu_utilization = 0.7
}
```

---

## Troubleshooting

### Queue Backed Up

**Symptom**: Tasks waiting in queue, not processing

**Solution**:
```bash
# 1. Check worker health
docker logs hey-sh-storage-worker

# 2. Increase replicas
kubectl scale deployment storage-worker --replicas=5

# 3. Check for stuck activities
tctl activity ls -task-queue storage-queue
```

### Wrong Queue Selected

**Symptom**: Workflow running too slow

**Solution**:
- Verify `task_queue` parameter in workflow execution
- Check activity registrations match queue names
- Monitor metrics to identify bottlenecks

### Resource Exhaustion

**Symptom**: Workers crashing or memory errors

**Solution**:
- Increase memory allocation in docker-compose or Terraform
- Reduce concurrent activity limits
- Add more worker replicas

---

## Local Development Setup

### Start All Services with Correct Queues

```bash
# Using docker-compose (includes all 3 queues)
docker-compose up

# Or start individually
docker-compose up api temporal
docker-compose up ai-worker
docker-compose up storage-worker
docker-compose up general-worker

# View Temporal UI
open http://temporal.hey.local
```

### Testing Different Queues Locally

```python
import asyncio
from temporalio.client import Client

async def test_queues():
    client = await Client.connect("localhost:7233")

    # Test each queue
    for queue in ["ai-processing-queue", "storage-queue", "general-queue"]:
        result = await client.execute_workflow(
            "TestWorkflow",
            id=f"test-{queue}",
            task_queue=queue,
        )
        print(f"{queue}: {result}")
```

---

## Production Deployment

### Deploy with Terraform

```bash
cd terraform/prod

# Plan deployment
terraform plan -var-file=terraform.tfvars

# Apply configuration
terraform apply -var-file=terraform.tfvars
```

### Monitor Production Queues

```bash
# Set up monitoring alerts
gcloud monitoring policies create \
  --display-name="Temporal Queue Backlog" \
  --condition-display-name="Queue backlog > 1000"
```

---

## Best Practices

1. **Always specify task_queue** when starting workflows
2. **Size workers appropriately** - don't over-provision
3. **Monitor queue metrics** regularly
4. **Auto-scale based on queue depth**, not just CPU
5. **Route tasks intelligently**:
   - Heavy compute → AI queue
   - I/O intensive → Storage queue
   - Everything else → General queue
6. **Set activity timeouts** to prevent orphaned tasks
7. **Use circuit breakers** for external service calls

---

## References

- [Temporal Task Queues](https://docs.temporal.io/concepts/what-is-a-task-queue)
- [Worker Configuration](https://docs.temporal.io/develop/python/workers)
- [Capacity Planning](https://docs.temporal.io/concepts/what-is-a-temporal-cluster#capacity-planning)

---

**Last Updated**: October 21, 2025
**Status**: Production Ready

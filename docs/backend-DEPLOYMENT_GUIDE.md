# Document Workflow Multi-Queue Deployment Guide

## Arkitektur Översikt

Detta system använder Temporal workflows med tre separata köer för olika typer av arbetsbelastningar:

### 1. AI Processing Queue (`ai-processing-queue`)
**Syfte**: Hanterar AI-modellkörningar, dokumentanalys och NLP-uppgifter

**Resurskrav**:
- GPU: 1x NVIDIA GPU (för modellacceleration)
- RAM: 16 GB
- CPU: 4 kärnor
- Modeller: Claude Haiku (default), GPT-4, eller anpassade modeller

**Activities**:
- `assess_document_relevance` - Bedömer dokuments relevans
- `extract_document_topics` - Extraherar ämnen från dokument
- `generate_summary_for_notification` - Genererar sammanfattningar
- `execute_ai_agent_activity` - Kör generiska AI-uppgifter

### 2. Storage Queue (`storage-queue`)
**Syfte**: Hanterar databasoperationer, fillagring och indexering

**Resurskrav**:
- GPU: Ej nödvändigt
- RAM: 8 GB
- CPU: 2 kärnor
- Snabb disk I/O rekommenderas
- Persistent volym för cache

**Activities**:
- `index_to_weaviate` - Indexerar till vektordatabas
- `update_neo4j_graph` - Uppdaterar grafdatabas
- `store_document_metadata` - Lagrar metadata
- `archive_rejected_document` - Arkiverar dokument

### 3. General Queue (`general-queue`)
**Syfte**: Hanterar workflows, notifieringar och lättviktiga uppgifter

**Resurskrav**:
- GPU: Ej nödvändigt
- RAM: 4 GB
- CPU: 2 kärnor
- Kan skalas horisontellt enkelt

**Workflows & Activities**:
- Alla huvudworkflows körs här
- `notify_stakeholders` - Skickar notifieringar
- `get_next_controller` - Round-robin tilldelning
- Human-in-the-loop koordination

## Deployment Alternativ

### 1. Lokal Development (Docker Compose)

```bash
# Starta alla tjänster
docker-compose -f deployments/docker-compose.multi-queue.yml up

# Starta specifik worker-typ
docker-compose -f deployments/docker-compose.multi-queue.yml up ai-worker

# Skala workers
docker-compose -f deployments/docker-compose.multi-queue.yml up --scale general-worker=5
```

### 2. Kubernetes Deployment

```bash
# Skapa namespace och configs
kubectl apply -f deployments/k8s/configmaps.yaml

# Deploya workers
kubectl apply -f deployments/k8s/ai-worker-deployment.yaml
kubectl apply -f deployments/k8s/storage-worker-deployment.yaml
kubectl apply -f deployments/k8s/general-worker-deployment.yaml

# Övervaka deployment
kubectl get pods -n temporal-workers
kubectl top pods -n temporal-workers
```

### 3. Cloud Run (GCP)

För AI Worker med GPU:
```bash
gcloud run deploy ai-worker \
  --image gcr.io/${PROJECT_ID}/hey-sh-ai-worker \
  --platform managed \
  --region us-central1 \
  --memory 16Gi \
  --cpu 4 \
  --gpu 1 \
  --gpu-type nvidia-tesla-t4 \
  --set-env-vars WORKER_TYPES=ai-processing
```

För Storage Worker:
```bash
gcloud run deploy storage-worker \
  --image gcr.io/${PROJECT_ID}/hey-sh-storage-worker \
  --platform managed \
  --region us-central1 \
  --memory 8Gi \
  --cpu 2 \
  --set-env-vars WORKER_TYPES=storage \
  --min-instances 2 \
  --max-instances 10
```

För General Worker:
```bash
gcloud run deploy general-worker \
  --image gcr.io/${PROJECT_ID}/hey-sh-worker \
  --platform managed \
  --region us-central1 \
  --memory 4Gi \
  --cpu 2 \
  --set-env-vars WORKER_TYPES=general \
  --min-instances 3 \
  --max-instances 20
```

## Workflow Konfiguration

### Domain-specifik anpassning

När en ny domän skapas kan ägaren konfigurera:

```python
domain_config = {
    "relevance_threshold": 7.0,        # Tröskel för godkännande
    "auto_approve_threshold": 8.5,     # Auto-godkänn höga scores
    "auto_reject_threshold": 4.0,      # Auto-avvisa låga scores
    "use_ai_controller": False,        # Använd AI som controller
    "controller_pool": ["user1", "user2"],  # Controllers för round-robin
    "ai_model_override": "claude-3-opus"    # Override AI-modell
}
```

### Rollhierarki

```
Admin → Controller → Contributor
  ↓         ↓           ↓
 Alla    Godkänna    Ladda upp
rättig-  + rösta     dokument
 heter               + rösta
```

## Monitorering

### Temporal Web UI
Besök `http://localhost:8088` för att övervaka:
- Aktiva workflows
- Worker status per kö
- Workflow historik
- Failed activities

### Prometheus Metrics
Workers exponerar metrics på `/metrics`:
- `temporal_worker_task_slots_available`
- `temporal_activity_execution_duration`
- `temporal_workflow_task_execution_duration`

### Health Checks
Alla workers har health endpoints på `:8080/health`:
```bash
curl http://localhost:8080/health
```

## Skalning

### Vertikal skalning (större resurser)
- AI Workers: Uppgradera GPU (T4 → V100 → A100)
- Storage Workers: Öka minne och disk IOPS
- General Workers: Vanligtvis inte nödvändigt

### Horisontell skalning (fler instanser)
- AI Workers: Max 5 (GPU-kostnad)
- Storage Workers: Max 10 (databaskopplingar)
- General Workers: Max 20+ (lätt arbetsbelastning)

### Auto-scaling triggers
- CPU > 70% för AI workers
- Memory > 80% för storage workers
- CPU > 50% för general workers

## Felsökning

### Worker startar inte
```bash
# Kontrollera logs
kubectl logs -n temporal-workers deployment/ai-processing-worker

# Verifiera miljövariabler
kubectl describe deployment ai-processing-worker -n temporal-workers
```

### Activities timeout
- Öka timeout i WorkflowConfig
- Kontrollera worker resurser
- Verifiera nätverksanslutningar

### GPU inte tillgänglig
```bash
# Kontrollera NVIDIA drivers
nvidia-smi

# Verifiera CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

## Säkerhet

### Secrets Management
- Använd Kubernetes Secrets eller GCP Secret Manager
- Rotera API-nycklar regelbundet
- Begränsa åtkomst per worker-typ

### Network Policies
```yaml
# Exempel: AI workers får bara prata med Temporal
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ai-worker-network-policy
spec:
  podSelector:
    matchLabels:
      worker-type: ai-processing
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: temporal-system
```

## Kostnadsoptimering

### GPU-användning
- Använd spot/preemptible instanser för development
- Dela GPU mellan workers med MIG (Multi-Instance GPU)
- Överväg CPU-only inference för enklare modeller

### Storage
- Arkivera gamla dokument till cold storage
- Komprimera embeddings
- Använd retention policies

### Compute
- Använd autoscaling aggressivt
- Stäng av dev-miljöer nattetid
- Använd ARM-baserade instanser för general workers

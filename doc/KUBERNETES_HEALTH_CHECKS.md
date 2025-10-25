# Kubernetes Health Checks and Self-Tests

This guide explains the comprehensive health check and self-test system for deployed pods.

## Overview

Every pod runs three types of health checks:

1. **Startup Probe** - Runs once at pod startup (60 second timeout)
2. **Readiness Probe** - Checks if pod can serve traffic (called every 5 seconds)
3. **Liveness Probe** - Checks if pod should be restarted (called every 10 seconds)

## Health Check Endpoints

### `/health` (Basic Check)
Simple health status - used by load balancers.

```bash
curl http://pod-ip:8000/health
# Returns: {"status": "healthy"}
```

### `/health/startup`
Pod initialization check - runs once before readiness checks start.

```bash
curl http://pod-ip:8000/health/startup
# Returns:
# {
#   "started": true,
#   "timestamp": "2024-01-15T10:30:00Z",
#   "system": {
#     "hostname": "pod-name",
#     "environment": "production",
#     "pod_name": "hey-sh-backend-abc123",
#     "pod_namespace": "production"
#   },
#   "checks": {
#     "temporal": {"status": "healthy", "message": "Connected to Temporal"},
#     "services": {"status": "healthy", "message": "All external services configured"}
#   }
# }
```

**Checked systems:**
- Temporal server connection
- Required environment variables
- External services configuration

### `/health/ready`
Pod readiness check - pod removed from load balancer if fails.

```bash
curl http://pod-ip:8000/health/ready
# Returns:
# {
#   "ready": true,
#   "timestamp": "2024-01-15T10:30:05Z",
#   "checks": {
#     "temporal": {"status": "healthy", "message": "Connected to Temporal"},
#     "databases": {"status": "healthy", "message": "All databases connected"},
#     "services": {"status": "degraded", "message": "1 configuration issue(s)"}
#   }
# }
```

**Checked systems:**
- Temporal server connection
- Database connectivity (Neo4j, Weaviate, PostgreSQL)
- External service availability

### `/health/live`
Pod liveness check - pod restarted if fails.

```bash
curl http://pod-ip:8000/health/live
# Returns:
# {
#   "alive": true,
#   "timestamp": "2024-01-15T10:30:10Z",
#   "checks": {
#     "temporal": {"status": "healthy", "message": "Connected to Temporal"}
#   }
# }
```

**Only checks:** Temporal critical service (minimal check for fast response)

## Probe Configuration

### API Server Probes

```yaml
# Startup probe - 60 second timeout
startupProbe:
  httpGet:
    path: /health/startup
    port: health
  periodSeconds: 2
  failureThreshold: 30  # 30 × 2 seconds = 60 seconds max

# Readiness probe - removes from load balancer after 15 seconds
readinessProbe:
  httpGet:
    path: /health/ready
    port: health
  periodSeconds: 5
  failureThreshold: 3  # 3 × 5 seconds = 15 seconds

# Liveness probe - restarts pod after 30 seconds
livenessProbe:
  httpGet:
    path: /health/live
    port: health
  periodSeconds: 10
  failureThreshold: 3  # 3 × 10 seconds = 30 seconds
```

### Worker Probes

Workers have identical probe configuration with adjusted timeouts for GPU initialization:

```yaml
startupProbe:
  failureThreshold: 40  # 40 × 3 seconds = 120 seconds (GPU init time)
```

## Pod Status Lifecycle

```
┌─────────────────────────────────────────────────────┐
│ Pod Created                                          │
├─────────────────────────────────────────────────────┤
│ INIT CONTAINERS RUN (startup-check)                │
│ ├─ Loop 30 times (wait max 60 seconds)             │
│ ├─ curl /health/startup on localhost:8000          │
│ ├─ Check for "started": true                       │
│ └─ Fail if not ready after 60 seconds              │
├─────────────────────────────────────────────────────┤
│ POD CONTAINERS START                               │
│ ├─ Startup Probe runs (every 2-3 seconds)         │
│ ├─ Pod stays NOT READY until startup passes       │
│ ├─ Timeout after 60 seconds → Pod restarts        │
│ └─ After success → Move to readiness checks       │
├─────────────────────────────────────────────────────┤
│ READINESS PROBE STARTS (every 5 seconds)           │
│ ├─ Pod added to load balancer if passes            │
│ ├─ Pod removed from load balancer if fails         │
│ └─ Continues indefinitely                           │
├─────────────────────────────────────────────────────┤
│ LIVENESS PROBE STARTS (every 10 seconds)           │
│ ├─ Restarts pod if fails 3 times (30 seconds)     │
│ └─ Runs continuously during pod lifetime           │
└─────────────────────────────────────────────────────┘
```

## Deployment Steps

### 1. Apply ConfigMap

```bash
kubectl apply -f k8s/config/configmap.yaml
```

### 2. Create Secrets

```bash
kubectl create secret generic api-secrets \
  --from-literal=openai_api_key=sk-... \
  --from-literal=anthropic_api_key=sk-ant-... \
  --from-literal=supabase_url=https://... \
  --from-literal=supabase_key=...
```

### 3. Deploy API Server

```bash
kubectl apply -f k8s/api/deployment.yaml
```

### 4. Deploy Workers

```bash
kubectl apply -f k8s/workers/deployment.yaml
```

### 5. Verify Deployments

```bash
# Watch rollout
kubectl rollout status deployment/hey-sh-backend

# Check pod status
kubectl get pods -l app=hey-sh-backend
kubectl describe pod <pod-name>

# Check health endpoints
kubectl port-forward svc/hey-sh-backend 8000:8000
curl http://localhost:8000/health/ready
```

## Monitoring Health Checks

### View Pod Events

```bash
# Show recent events
kubectl describe pod hey-sh-backend-abc123

# Watch events in real-time
kubectl get events --sort-by='.lastTimestamp'
```

### Check Probe Logs

```bash
# View pod logs
kubectl logs -f deployment/hey-sh-backend

# View startup check logs
kubectl logs <pod-name> -c startup-check

# View application logs
kubectl logs <pod-name> -c api
```

### Probe Failure Reasons

```bash
# Pod shows "Not Ready"
# → Check: kubectl describe pod <pod-name> | grep -A 5 "Readiness probe"

# Pod shows "CrashLoopBackOff"
# → Liveness probe failed 3 times, pod restarted
# → Check: kubectl logs <pod-name>

# Pod never becomes Ready
# → Startup probe timeout (>60 seconds)
# → Check: kubectl logs <pod-name> -c startup-check
```

## Health Status Codes

### Health Endpoint Status

- **200 OK** - Healthy/Ready/Alive
- **503 Service Unavailable** - Unhealthy/Not Ready/Not Alive

### Status Values

```
status: "healthy"      - All systems operating
status: "degraded"     - Some systems down, can operate
status: "unhealthy"    - Cannot operate, restart needed
```

## Common Issues and Solutions

### Issue: Startup Probe Timeout

**Symptoms:** Pod never becomes Ready, startup-check container fails after 60 seconds

**Solutions:**
1. Increase `failureThreshold` in startupProbe
2. Check Temporal connectivity: `kubectl logs <pod-name>`
3. Verify ConfigMap values: `kubectl get configmap hey-sh-config -o yaml`
4. Check network connectivity: `kubectl exec <pod-name> -- curl temporal-cloud.io:7233`

### Issue: Readiness Probe Failures

**Symptoms:** Pod goes into Ready → NotReady → Ready cycle

**Solutions:**
1. Check database connectivity
2. Verify network policies allow outbound traffic
3. Check resource utilization (CPU/memory limits)
4. Increase probe timeout: change `timeoutSeconds` from 3 to 5

### Issue: Liveness Probe Restarts

**Symptoms:** Pod continuously restarts (CrashLoopBackOff)

**Solutions:**
1. Increase liveness probe `initialDelaySeconds` (give app time to initialize)
2. Check Temporal connection issues
3. Review application logs
4. Increase `failureThreshold` to reduce restart sensitivity

### Issue: Workers Failing Startup

**Symptoms:** GPU workers timeout on startup

**Solutions:**
1. Verify GPU availability: `kubectl get nodes -o wide | grep gpu`
2. Check NVIDIA drivers: `kubectl run -it --image=nvidia/cuda:12.2.0 cuda-test -- nvidia-smi`
3. Increase GPU worker `failureThreshold` to 50+ (can take 2+ minutes)
4. Check resource requests match available resources

## Best Practices

### 1. **Health Check Configuration**

✅ **DO:**
- Start with conservative probe settings (longer timeouts)
- Gradually tighten probes after stability confirmed
- Match `periodSeconds` to check frequency needs

❌ **DON'T:**
- Use identical probe settings for startup, readiness, and liveness
- Set timeouts shorter than check duration needs
- Use aggressive failure thresholds

### 2. **Health Endpoint Implementation**

✅ **DO:**
- Keep `/health` endpoint fast (<100ms)
- Check only critical systems in liveness probe
- Return detailed info in startup/readiness probes

❌ **DON'T:**
- Make health endpoints slow or heavy
- Check slow operations in liveness probe
- Ignore transient errors

### 3. **Monitoring and Alerting**

✅ **DO:**
- Monitor pod restart rates
- Alert on repeated readiness failures
- Log startup probe activities

❌ **DON'T:**
- Ignore pod restarts (they indicate problems)
- Use only default Kubernetes metrics
- Skip application-level health metrics

## Integration with Cloud Build

The `cloudbuild.yaml` includes smoke tests that run after deployment:

```yaml
- name: smoke-tests
  args:
    - run
    - --rm
    - python:3.12
    - sh
    - -c
    - "python backend/test/smoke_test_staging.py"
  waitFor: ["deploy-workers"]
```

These run the same tests as the health checks but at the application level.

## Related Documentation

- [Kubernetes Probes Documentation](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Cloud Build Setup](./CLOUD_BUILD_SETUP.md)
- [Local Development](./DEVELOPMENT.md)

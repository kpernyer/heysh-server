# Temporal Cloud Setup Guide

This guide explains how your backend is configured to work with Temporal Cloud for production.

## Configuration

### Environment Variables

The following environment variables are required for Temporal Cloud:

```bash
# Temporal Cloud Configuration
TEMPORAL_ADDRESS='europe-west3.gcp.api.temporal.io:7233'
TEMPORAL_NAMESPACE='quickstart-heysh-knowledge.jnw2m'
TEMPORAL_API_KEY='your-temporal-api-key-here'
TEMPORAL_TASK_QUEUE='hey-sh-workflows'
```

These are already configured in your `.env` file.

### Connection Details

**API Key:**
- Expires: October 2025
- Account ID: jnw2m
- Region: europe-west3 (GCP)

**Namespace:** `quickstart-heysh-knowledge.jnw2m`

## How It Works

### Automatic TLS Detection

Both the API server (`service/api.py`) and worker (`worker/main.py`) automatically detect whether to use Temporal Cloud:

```python
# If TEMPORAL_API_KEY is set -> Use Temporal Cloud with TLS
if temporal_api_key:
    from temporalio.client import TLSConfig

    connect_config["tls"] = TLSConfig()
    connect_config["api_key"] = temporal_api_key
    logger.info("Using Temporal Cloud with TLS and API key authentication")
else:
    # If no API key -> Use local Temporal (docker)
    logger.info("Using local Temporal server (no TLS)")
```

This allows seamless switching between:
- **Local development:** Docker-based Temporal server (no API key needed)
- **Production:** Temporal Cloud (API key required)

## Testing the Connection

### 1. Test API Server Connection

```bash
cd backend
source ../.env
.venv/bin/uvicorn service.api:app --reload --port 8001
```

You should see:
```
Connecting to Temporal address=europe-west3.gcp.api.temporal.io:7233 namespace=quickstart-heysh-knowledge.jnw2m
Using Temporal Cloud with TLS and API key authentication
Connected to Temporal successfully
```

### 2. Test Worker Connection

```bash
cd backend
source ../.env
.venv/bin/python worker/main.py
```

You should see:
```
Starting Temporal worker address=europe-west3.gcp.api.temporal.io:7233 namespace=quickstart-heysh-knowledge.jnw2m task_queue=hey-sh-workflows
Using Temporal Cloud with TLS and API key authentication
Worker started successfully. Waiting for tasks...
```

### 3. Test Workflow Execution

Run a test workflow to verify end-to-end functionality:

```bash
./script/test_document_workflow.sh
```

This will:
1. Create a test domain
2. Trigger DocumentProcessing workflow
3. Monitor execution on Temporal Cloud
4. Display results

## Viewing Workflows in Temporal Cloud

**Temporal Cloud UI:**
- URL: https://cloud.temporal.io
- Login with your Temporal account
- Navigate to namespace: `quickstart-heysh-knowledge.jnw2m`
- View workflows, activities, and execution history

## Local Development vs Production

### Local Development (Docker)
```bash
# .env configuration for local
TEMPORAL_ADDRESS=localhost:7233
TEMPORAL_NAMESPACE=default
# TEMPORAL_API_KEY=  # Leave empty or comment out
```

Start local Temporal:
```bash
just dev  # Starts docker-compose with Temporal
```

### Production (Temporal Cloud)
```bash
# .env configuration for production
TEMPORAL_ADDRESS=europe-west3.gcp.api.temporal.io:7233
TEMPORAL_NAMESPACE=quickstart-heysh-knowledge.jnw2m
TEMPORAL_API_KEY=your-api-key-here
```

No need to run Docker - connects directly to Temporal Cloud.

## API Key Management

### Current API Key
- **Expiration:** October 2025
- **Type:** API Key (Bearer token)
- **Permissions:** Full access to namespace `quickstart-heysh-knowledge.jnw2m`

### Rotating API Keys

When the key expires (or for security rotation):

1. **Generate new API key in Temporal Cloud:**
   - Go to https://cloud.temporal.io
   - Navigate to Settings → API Keys
   - Create new API key
   - Copy the new key

2. **Update environment variables:**
   ```bash
   # Update .env file
   TEMPORAL_API_KEY='new-api-key-here'
   ```

3. **Restart services:**
   ```bash
   # Restart API
   killall uvicorn
   source ../.env && .venv/bin/uvicorn service.api:app --reload --port 8001

   # Restart worker
   killall python
   source ../.env && .venv/bin/python worker/main.py
   ```

## Deployment

### Environment Variables for Production

Ensure these are set in your deployment environment (Cloud Run, K8s, etc.):

```bash
TEMPORAL_ADDRESS=europe-west3.gcp.api.temporal.io:7233
TEMPORAL_NAMESPACE=quickstart-heysh-knowledge.jnw2m
TEMPORAL_API_KEY=<from-secrets-manager>
TEMPORAL_TASK_QUEUE=hey-sh-workflows
```

**Best Practices:**
- Store `TEMPORAL_API_KEY` in a secrets manager (Google Secret Manager, AWS Secrets Manager, etc.)
- Never commit API keys to git
- Use different API keys for staging vs production

### Worker Deployment

Workers must be deployed separately from the API:

```yaml
# Example K8s deployment for worker
apiVersion: apps/v1
kind: Deployment
metadata:
  name: temporal-worker
spec:
  replicas: 3  # Scale based on load
  template:
    spec:
      containers:
      - name: worker
        image: your-registry/hey-sh-worker:latest
        command: ["python", "worker/main.py"]
        env:
        - name: TEMPORAL_ADDRESS
          value: "europe-west3.gcp.api.temporal.io:7233"
        - name: TEMPORAL_NAMESPACE
          value: "quickstart-heysh-knowledge.jnw2m"
        - name: TEMPORAL_API_KEY
          valueFrom:
            secretKeyRef:
              name: temporal-secrets
              key: api-key
```

## Monitoring & Observability

### Temporal Cloud Dashboard
- **Workflows:** View all running and completed workflows
- **Activities:** Track individual activity executions
- **Metrics:** Workflow duration, success/failure rates
- **Search:** Query workflows by ID, type, or status

### Logs
Both API and worker log Temporal connection status:
- `Using Temporal Cloud with TLS and API key authentication` - Cloud mode
- `Using local Temporal server (no TLS)` - Local mode

### Alerts
Consider setting up alerts for:
- Workflow failures
- Worker disconnections
- High workflow latency
- API key expiration warnings

## Troubleshooting

### Connection Refused
**Error:** `Connection refused to europe-west3.gcp.api.temporal.io:7233`

**Solutions:**
1. Check API key is valid and not expired
2. Verify network connectivity (firewall, DNS)
3. Ensure `TEMPORAL_API_KEY` environment variable is set

### Authentication Failed
**Error:** `Authentication failed` or `Invalid API key`

**Solutions:**
1. Verify API key is correct in `.env`
2. Check API key hasn't expired
3. Ensure key has permissions for the namespace

### TLS Certificate Errors
**Error:** `SSL certificate verification failed`

**Solutions:**
1. Update `temporalio` package: `pip install --upgrade temporalio`
2. Check system CA certificates are up to date
3. Verify you're using `TLSConfig()` (without custom certs)

### Worker Not Picking Up Tasks
**Error:** Worker running but workflows stuck

**Solutions:**
1. Verify `TEMPORAL_TASK_QUEUE` matches in worker and API
2. Check worker is connected to same namespace as API
3. Ensure worker has all required activities registered

## Cost Optimization

### Temporal Cloud Costs
- Based on: Actions (workflow/activity executions)
- Free tier: 1M actions/month
- Monitor usage in Temporal Cloud dashboard

### Best Practices
1. **Batch operations** - Process multiple items in single workflow
2. **Optimize activities** - Reduce unnecessary activity calls
3. **Use local dev** - Use Docker for development, Cloud for production
4. **Monitor costs** - Set up billing alerts in Temporal Cloud

## Summary

✅ **Configured:**
- Temporal Cloud connection with TLS
- API key authentication
- Automatic local/cloud switching
- Production-ready worker setup

✅ **Next Steps:**
1. Test connection with provided commands
2. Monitor workflows in Temporal Cloud UI
3. Set up production deployment with secrets management
4. Configure monitoring and alerts

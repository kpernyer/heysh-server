# Testing Guide - Document Workflow System

## 🧪 Testing Strategy

### Test Pyramid
```
         /\
        /E2E\        <- End-to-end tests (10%)
       /------\
      /Integr. \     <- Integration tests (30%)
     /----------\
    /   Unit     \   <- Unit tests (60%)
   /--------------\
```

## 🏃 Quick Start Testing

### 1. Local Testing
```bash
# Start test environment
just dev

# Run all tests
just test

# Run specific test types
just test-unit          # Unit tests only
just test-integration   # Integration tests
just test-e2e          # End-to-end tests
just test-load         # Load testing
```

### 2. Testing with Docker
```bash
# Complete test suite with Docker
just test-local

# This will:
# - Start all required services
# - Run unit, integration, and E2E tests
# - Generate coverage report
# - Clean up after tests
```

## 📋 Test Types

### Unit Tests
Location: `test/unit/`

Test individual functions and methods in isolation:
```python
# Example: test/unit/test_activities.py
def test_assess_document_relevance():
    result = assess_document_relevance(
        document_id="test-123",
        domain_criteria={"topic": "AI"},
        ai_config={"model": "mock"}
    )
    assert result["relevance_score"] >= 0
    assert result["relevance_score"] <= 10
```

### Integration Tests
Location: `test/test_workflows.py`

Test workflow execution with mocked services:
```python
# Run integration tests
pytest test/test_workflows.py -v
```

Key scenarios:
- Auto-approve high score documents
- Auto-reject low score documents
- Human controller review flow
- AI controller review flow
- Error handling

### End-to-End Tests
Complete workflow testing with real services:
```python
# Run E2E test
pytest test/test_workflows.py::test_end_to_end_document_flow -v
```

### Load Tests
Performance testing under load:
```bash
# Run load test (100 workflows, 10 concurrent)
python test/load_test.py 100 10

# Heavy load test
python test/load_test.py 1000 50
```

## 🔬 Testing Locally

### Prerequisites
```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Start local services
docker-compose -f docker-compose.test.yml up -d
```

### Running Tests Step by Step

1. **Start Mock Services**
```bash
# Start mock AI service (replaces OpenAI/Anthropic)
docker-compose -f docker-compose.test.yml up mock-ai -d

# Verify mock is running
curl http://localhost:8001/health
```

2. **Configure Test Environment**
```bash
export USE_MOCK_AI=true
export DEFAULT_RELEVANCE_SCORE=7.5
export RANDOMIZE_SCORES=false
```

3. **Run Specific Test Suites**
```bash
# Test workflow with high score (auto-approve)
export DEFAULT_RELEVANCE_SCORE=9.0
pytest test/test_workflows.py::test_auto_approve_high_score_document -v

# Test workflow with low score (auto-reject)
export DEFAULT_RELEVANCE_SCORE=3.0
pytest test/test_workflows.py::test_auto_reject_low_score_document -v

# Test human review flow
export DEFAULT_RELEVANCE_SCORE=6.0
pytest test/test_workflows.py::test_human_controller_review_flow -v
```

## ☁️ Cloud Testing (Staging)

### Deploy to Staging
```bash
# Set up GCP credentials
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="europe-north1"

# Deploy staging environment
just deploy-staging

# Run smoke tests
python test/smoke_test_staging.py
```

### Staging Test Checklist
- [ ] Temporal connection works
- [ ] All worker types are healthy
- [ ] Workflow execution succeeds
- [ ] Database connections work
- [ ] Monitoring metrics appear
- [ ] Alerts are configured

### Progressive Deployment Testing

1. **Canary Testing**
```bash
# Deploy canary version (10% traffic)
kubectl set image deployment/general-worker \
  general-worker=gcr.io/$PROJECT/hey-sh-worker:canary \
  -n temporal-workers

# Monitor canary metrics
kubectl logs -n temporal-workers -l version=canary -f

# If successful, roll out fully
kubectl set image deployment/general-worker \
  general-worker=gcr.io/$PROJECT/hey-sh-worker:canary \
  -n temporal-workers --all
```

2. **Blue-Green Testing**
```bash
# Deploy green environment
kubectl apply -f deployments/k8s/green/

# Test green environment
python test/smoke_test_staging.py --env=green

# Switch traffic to green
kubectl patch service general-worker \
  -p '{"spec":{"selector":{"version":"green"}}}'

# Remove blue environment after verification
kubectl delete -f deployments/k8s/blue/
```

## 🔍 Debugging Failed Tests

### 1. Check Worker Logs
```bash
# Local
docker-compose -f docker-compose.test.yml logs test-worker

# Staging/Production
kubectl logs -n temporal-workers -l worker-type=general --tail=100
```

### 2. Check Temporal Web UI
```bash
# Local
open http://localhost:8088

# Staging (port forward)
kubectl port-forward -n temporal-system svc/temporal-web 8088:8088
```

### 3. Debug Specific Workflow
```python
# Debug script
from temporalio.client import Client

async def debug_workflow(workflow_id):
    client = await Client.connect("localhost:7233")
    handle = client.get_workflow_handle(workflow_id)

    # Get status
    status = await handle.query("get_status")
    print(f"Status: {status}")

    # Get history
    async for event in handle.fetch_history_events():
        print(event)
```

### 4. Common Issues

**Issue: Workflow stuck in UNDER_REVIEW**
```bash
# Send review signal manually
temporal workflow signal \
  --workflow-id=test-workflow-123 \
  --name=submit_review \
  --input='{"approved":true,"feedback":"Manual approval"}'
```

**Issue: Activity timeout**
```python
# Increase timeout in workflow
start_to_close_timeout=timedelta(minutes=10)  # Increase from 5
```

**Issue: Mock AI not returning expected score**
```bash
# Check mock AI configuration
curl http://localhost:8001/api/v1/models

# Test mock AI directly
curl -X POST http://localhost:8001/api/v1/ai/execute \
  -H "Content-Type: application/json" \
  -d '{"function_name":"assess_relevance","inputs":{}}'
```

## 📊 Test Coverage

### Generate Coverage Report
```bash
# Run tests with coverage
pytest test/ \
  --cov=workflow \
  --cov=activity \
  --cov-report=html:test-results/coverage \
  --cov-report=term

# View coverage report
open test-results/coverage/index.html
```

### Coverage Goals
- Unit tests: >80%
- Integration tests: >60%
- Critical paths: 100%

## 📈 Performance Testing

### Baseline Performance
```yaml
Expected Performance:
  - Document processing: < 5s (p95)
  - AI assessment: < 3s (p95)
  - Database indexing: < 2s (p95)
  - Workflow completion: < 15s (p95)
  - Throughput: > 100 docs/min
```

### Load Test Scenarios

1. **Normal Load**
```bash
python test/load_test.py \
  --workflows=100 \
  --concurrent=10 \
  --duration=5m
```

2. **Peak Load**
```bash
python test/load_test.py \
  --workflows=1000 \
  --concurrent=50 \
  --duration=15m
```

3. **Stress Test**
```bash
python test/load_test.py \
  --workflows=5000 \
  --concurrent=100 \
  --duration=30m
```

### Monitoring During Tests
```bash
# Watch metrics
watch -n 1 'kubectl top pods -n temporal-workers'

# Monitor queue latency
curl -s http://localhost:9090/api/v1/query?query=temporal_workflow_task_schedule_to_start_latency_seconds

# Check error rate
curl -s http://localhost:9090/api/v1/query?query=rate(temporal_workflow_failed_total[5m])
```

## 🚨 Pre-Production Checklist

- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] E2E tests pass in staging
- [ ] Load tests meet performance targets
- [ ] Security scan completed
- [ ] Dependencies updated
- [ ] Documentation updated
- [ ] Monitoring configured
- [ ] Alerts tested
- [ ] Rollback plan prepared

## 🔄 Continuous Testing

### GitHub Actions Workflow
```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: just test-local
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## 📝 Test Documentation

### Writing New Tests
```python
# Template for new workflow test
class TestNewFeature:
    @pytest.mark.asyncio
    async def test_feature_happy_path(self, temporal_client, test_worker):
        """Test description."""
        # Arrange
        input = create_test_input()

        # Act
        result = await run_workflow(input)

        # Assert
        assert result.success is True
        assert_expected_side_effects()
```

### Test Naming Convention
- `test_<feature>_<scenario>_<expected_result>`
- Example: `test_document_review_ai_controller_approves`

## 🆘 Getting Help

### Resources
- Temporal Testing Docs: https://docs.temporal.io/docs/python/testing
- Pytest Docs: https://docs.pytest.org/
- Load Testing Guide: internal/docs/load-testing.md

### Contact
- Slack: #hey-sh-workflow-dev
- Email: workflow-team@example.com

# Backend Architecture & Integration Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (React/Vite + Lovable)                                │
│  - Domain management UI                                         │
│  - Document upload                                              │
│  - Q&A interface                                                │
│  - Role-based collaboration                                     │
└────────────────┬────────────────────────────────────────────────┘
                 │ HTTP REST (or GraphQL)
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│  FastAPI (service/api.py) - YOUR MIDDLE LAYER                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Domain Management (TODO)                                   │ │
│  │  - Create/list/update domains                              │ │
│  │  - Add/remove members                                      │ │
│  │  - Role-based access control                               │ │
│  ├───────────────────────────────────────────────────────────┤ │
│  │ Workflow Triggers (EXISTS)                                 │ │
│  │  - Document processing                                     │ │
│  │  - Question answering                                      │ │
│  │  - Quality reviews                                         │ │
│  ├───────────────────────────────────────────────────────────┤ │
│  │ Status & Monitoring                                        │ │
│  │  - Workflow status queries                                 │ │
│  │  - SSE/WebSockets for real-time updates (TODO)             │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────┬────────────────────────────────────────────────┘
                 │ Temporal Client
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│  Temporal Server (Orchestration)                                │
│  - Durable workflow execution                                   │
│  - Activity retries & timeouts                                  │
│  - Human-in-the-loop signals                                    │
└────────────────┬────────────────────────────────────────────────┘
                 │ Activities
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│  Workers (worker/main.py)                                       │
│  ┌───────────────┬────────────────┬───────────────────────────┐│
│  │ Documents     │ Vectors        │ Knowledge Graph           ││
│  │ (Supabase)    │ (Weaviate)     │ (Neo4j)                   ││
│  └───────────────┴────────────────┴───────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ LLM (OpenAI GPT-4o)                                          ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Answer to Your Question: Do We Need Another Middle Layer?

**NO.** FastAPI IS your middle layer. It's the perfect place for:

1. **Request validation** (Pydantic schemas)
2. **Authentication/authorization** (Supabase Auth integration)
3. **Domain/role management** (business logic)
4. **Workflow orchestration** (Temporal client)
5. **REST and/or GraphQL endpoints** (FastAPI + Strawberry)

## What You Need to Add

### 1. Domain Management Endpoints (Priority: HIGH)

Add these to `service/api.py`:

```python
# Domains
POST   /api/v1/domains              # Create domain
GET    /api/v1/domains              # List user's domains
GET    /api/v1/domains/{domain_id}  # Get domain details
PATCH  /api/v1/domains/{domain_id}  # Update domain
DELETE /api/v1/domains/{domain_id}  # Delete domain

# Domain Members & Roles
POST   /api/v1/domains/{domain_id}/members       # Add member (contributor/controller/visitor)
GET    /api/v1/domains/{domain_id}/members       # List members
PATCH  /api/v1/domains/{domain_id}/members/{uid} # Update member role
DELETE /api/v1/domains/{domain_id}/members/{uid} # Remove member

# Domain Documents
GET    /api/v1/domains/{domain_id}/documents     # List domain documents
POST   /api/v1/domains/{domain_id}/documents     # Upload document (triggers workflow)

# Domain Q&A
GET    /api/v1/domains/{domain_id}/questions     # List questions
POST   /api/v1/domains/{domain_id}/questions     # Ask question (triggers workflow)
```

### 2. Authentication & Authorization

Integrate Supabase Auth:

```python
# Add to service/api.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    """Verify JWT token from Supabase."""
    # Verify with Supabase
    # Return user object
    pass

async def check_domain_permission(
    domain_id: str,
    user_id: str,
    required_role: str
):
    """Check if user has required role in domain."""
    # Query Supabase for user's role in domain
    # Raise 403 if insufficient permissions
    pass
```

### 3. Real-Time Updates (Priority: MEDIUM)

Add Server-Sent Events or WebSockets for workflow progress:

```python
from fastapi import Response
from sse_starlette.sse import EventSourceResponse

@app.get("/api/v1/workflows/{workflow_id}/events")
async def workflow_events(workflow_id: str):
    """Stream workflow events to frontend."""
    async def event_generator():
        while True:
            # Poll Temporal for workflow status
            # Yield status updates
            yield {"data": json.dumps(status)}
            await asyncio.sleep(1)

    return EventSourceResponse(event_generator())
```

### 4. GraphQL (Optional with Strawberry)

If you want GraphQL alongside REST:

```python
# Add to service/api.py
import strawberry
from strawberry.fastapi import GraphQLRouter

@strawberry.type
class Domain:
    id: str
    name: str
    description: str
    members: list["Member"]

@strawberry.type
class Query:
    @strawberry.field
    async def domain(self, id: str) -> Domain:
        # Fetch domain
        pass

schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)

app.include_router(graphql_app, prefix="/graphql")
```

**Recommendation**: Start with REST, add GraphQL only if frontend needs it.

## Testing Your Backend

### Option 1: Bash Script (Quick Tests)

```bash
cd backend
./script/test_workflows.sh
```

### Option 2: Python CLI (More Control)

```bash
cd backend

# Test document upload
python script/workflow_client.py upload-doc \
  --domain-id my-domain \
  --file-path documents/test.pdf

# Ask a question
python script/workflow_client.py ask \
  --domain-id my-domain \
  --question "What are the key topics?"

# Check workflow status
python script/workflow_client.py status --workflow-id doc-123456

# Health check
python script/workflow_client.py health
```

### Option 3: cURL (Raw HTTP)

```bash
# Upload document
curl -X POST http://localhost:8001/api/v1/documents \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "doc-123",
    "domain_id": "my-domain",
    "file_path": "test.pdf"
  }'

# Ask question
curl -X POST http://localhost:8001/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "question_id": "q-456",
    "question": "What is the main topic?",
    "domain_id": "my-domain",
    "user_id": "user-789"
  }'

# Check workflow status
curl http://localhost:8001/api/v1/workflows/doc-123
```

## Frontend Integration

### From Lovable/React Frontend

```typescript
// Example: Upload document
const uploadDocument = async (domainId: string, file: File) => {
  // 1. Upload file to Supabase Storage
  const { data: storageData } = await supabase.storage
    .from('documents')
    .upload(`${domainId}/${file.name}`, file);

  // 2. Trigger backend workflow
  const response = await fetch('http://localhost:8001/api/v1/documents', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      document_id: crypto.randomUUID(),
      domain_id: domainId,
      file_path: storageData.path,
    }),
  });

  const { workflow_id } = await response.json();

  // 3. Poll or subscribe to workflow status
  const statusResponse = await fetch(
    `http://localhost:8001/api/v1/workflows/${workflow_id}`
  );
  return statusResponse.json();
};
```

## Data Flow Example: Domain Collaboration

### User Uploads Document

1. **Frontend** → Upload file to Supabase Storage
2. **Frontend** → POST `/api/v1/domains/{domain_id}/documents`
3. **FastAPI** → Check user has "contributor" role in domain
4. **FastAPI** → Start `DocumentProcessingWorkflow` in Temporal
5. **Temporal** → Execute activities:
   - Download document from Supabase
   - Extract text & metadata
   - Generate embeddings (OpenAI)
   - Index in Weaviate
   - Update Neo4j graph (link to domain, contributors)
6. **FastAPI** → Return workflow ID to frontend
7. **Frontend** → Subscribe to workflow events (SSE/WebSocket)
8. **Temporal** → Notify "controllers" for review if needed

### User Asks Question

1. **Frontend** → POST `/api/v1/domains/{domain_id}/questions`
2. **FastAPI** → Check user has access to domain
3. **FastAPI** → Start `QuestionAnsweringWorkflow`
4. **Temporal** → Execute activities:
   - Vector search in Weaviate (domain documents only)
   - Graph traversal in Neo4j (related docs)
   - Generate answer with LLM (GPT-4o)
   - Calculate confidence score
   - If low confidence → Create review task for "controllers"
5. **Temporal** → Return answer (or mark for review)
6. **Frontend** → Display answer (or "Under Review" status)

## Role-Based Workflow Collaboration

### Roles

- **Visitor**: Read-only access, can ask questions
- **Contributor**: Can upload documents, ask questions
- **Controller**: All contributor permissions + review/approve content

### Human-in-the-Loop Patterns

Temporal supports this natively:

```python
@workflow.defn
class QualityReviewWorkflow:
    @workflow.run
    async def run(self, review_id: str):
        # 1. Assign to controller
        await workflow.execute_activity(assign_review_activity, ...)

        # 2. Wait for human decision (can wait days/weeks)
        decision = await workflow.wait_condition(
            lambda: self.review_decision is not None,
            timeout=timedelta(days=7)
        )

        # 3. Apply decision
        if decision == "approve":
            await workflow.execute_activity(approve_content_activity, ...)
        elif decision == "reject":
            await workflow.execute_activity(reject_content_activity, ...)
```

Frontend signals the decision:

```python
@app.post("/api/v1/reviews/{review_id}/decision")
async def submit_review_decision(review_id: str, decision: str):
    """Controller submits review decision."""
    # Signal Temporal workflow
    handle = temporal_client.get_workflow_handle(f"review-{review_id}")
    await handle.signal("review_decision", decision)
```

## Next Steps

### Immediate (To Connect Frontend ↔ Backend)

1. **Add domain CRUD endpoints** to `service/api.py`
2. **Integrate Supabase Auth** for user authentication
3. **Add role checks** to all domain endpoints
4. **Test with curl/scripts** before connecting frontend

### Near-Term

5. **Add SSE/WebSocket** for real-time workflow updates
6. **Frontend integration** - Call backend API from Lovable
7. **End-to-end test** - Upload doc → Ask question → Review answer

### Optional

8. **Add GraphQL** with Strawberry if frontend prefers it
9. **Add CLI tool** for admin operations
10. **Add monitoring** (Prometheus/Grafana for workflow metrics)

## Conclusion

**You don't need another layer.** FastAPI is your middle layer. It bridges:

- **North**: Frontend (Lovable/React) via REST/GraphQL
- **South**: Temporal workflows for orchestration
- **East**: Supabase for auth, storage, metadata
- **West**: Neo4j, Weaviate for knowledge graph & search

Focus on adding domain management and role-based access control to FastAPI, and you'll have everything you need.

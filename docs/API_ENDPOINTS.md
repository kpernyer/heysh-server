# Hey.sh Backend API Reference

Complete API specification for the FastAPI backend. The backend orchestrates all business logic and exposes these endpoints to the frontend.

## Architecture

```
Frontend (React/Vite)
    ↓
    ├→ FastAPI Backend (this API)
    │   ├→ Temporal (workflow orchestration - internal)
    │   ├→ Neo4j (knowledge graph - internal)
    │   └→ Weaviate (semantic search - internal)
    └→ Supabase (auth, storage, data - direct)
```

**Important:** Frontend calls this API and Supabase directly. It never calls Temporal, Neo4j, or Weaviate directly.

---

## Base URL

- **Local Development:** `http://localhost:8000`
- **Production:** `http://api.hey.local` (or your domain)

## Authentication

All endpoints require authentication via Supabase JWT tokens (passed as Bearer token in Authorization header).

---

## Core Endpoints

### Health & Status

#### Get Health Status
```
GET /health
```

Returns the health status of the backend service.

**Response:**
```json
{
  "status": "healthy"
}
```

#### Get Root
```
GET /
```

Returns API information.

**Response:**
```json
{
  "message": "Hey.sh Backend API",
  "version": "0.1.0"
}
```

---

## Workflow Execution Endpoints

These endpoints trigger asynchronous workflows via Temporal.

### Document Processing

#### Upload Document and Trigger Processing
```
POST /api/v1/documents
Status: 202 Accepted (async operation)
```

Upload a document and start the processing workflow.

**Request Body:**
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "domain_id": "456e4567-e89b-12d3-a456-426614174001",
  "file_path": "domain-456/document-123.pdf"
}
```

**Response:**
```json
{
  "workflow_id": "doc-123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "message": "Document processing started"
}
```

**What happens internally:**
1. Downloads document from Supabase Storage
2. Extracts text and metadata
3. Generates embeddings
4. Indexes in Weaviate (semantic search)
5. Updates Neo4j knowledge graph
6. Updates document status in Supabase

---

### Question Answering

#### Ask Question and Trigger Q&A Workflow
```
POST /api/v1/questions
Status: 202 Accepted (async operation)
```

Ask a question and start the question-answering workflow.

**Request Body:**
```json
{
  "question_id": "789e4567-e89b-12d3-a456-426614174002",
  "question": "What is the process for deploying to production?",
  "domain_id": "456e4567-e89b-12d3-a456-426614174001",
  "user_id": "012e4567-e89b-12d3-a456-426614174003"
}
```

**Response:**
```json
{
  "workflow_id": "question-789e4567-e89b-12d3-a456-426614174002",
  "status": "processing",
  "message": "Question answering started"
}
```

**What happens internally:**
1. Searches relevant documents (Weaviate semantic search)
2. Finds related documents via Neo4j graph queries
3. Generates answer using LLM
4. Calculates confidence score
5. Creates review task if confidence is low

---

### Quality Review

#### Submit Review and Trigger Review Workflow
```
POST /api/v1/reviews
Status: 202 Accepted (async operation)
```

Submit a review for a document or answer.

**Request Body:**
```json
{
  "review_id": "345e4567-e89b-12d3-a456-426614174004",
  "reviewable_type": "document",
  "reviewable_id": "123e4567-e89b-12d3-a456-426614174000",
  "domain_id": "456e4567-e89b-12d3-a456-426614174001"
}
```

**Response:**
```json
{
  "workflow_id": "review-345e4567-e89b-12d3-a456-426614174004",
  "status": "processing",
  "message": "Quality review started"
}
```

**What happens internally:**
1. Assigns review to domain admin/controller
2. Waits for review decision (via Temporal workflow)
3. Applies decision (approve/reject/rollback)
4. Updates quality scores in Supabase
5. Notifies contributor

---

### Workflow Status

#### Get Workflow Status
```
GET /api/v1/workflows/{workflow_id}
```

Get the current status of a running workflow.

**Response:**
```json
{
  "workflow_id": "doc-123e4567-e89b-12d3-a456-426614174000",
  "status": "RUNNING",
  "type": "DocumentProcessingWorkflow"
}
```

**Possible statuses:**
- `RUNNING` - Workflow is executing
- `COMPLETED` - Workflow finished successfully
- `FAILED` - Workflow failed
- `TIMED_OUT` - Workflow timed out
- `TERMINATED` - Workflow was terminated

---

## Data Management Endpoints

These endpoints manage domain, workflow, and document data stored in Supabase.

### Workflow Management

#### List Workflows
```
GET /api/v1/workflows
GET /api/v1/workflows?domain_id={domain_id}
```

List all workflows or filter by domain.

**Query Parameters:**
- `domain_id` (optional) - Filter by domain UUID

**Response:**
```json
{
  "workflows": [
    {
      "id": "workflow-123",
      "name": "Document Processing",
      "description": "Process and index documents",
      "domain_id": "domain-456",
      "yaml_definition": { "version": "1.0", "steps": [] },
      "is_active": true,
      "created_at": "2024-10-18T10:30:00Z"
    }
  ],
  "count": 1
}
```

#### Get Workflow
```
GET /api/v1/workflows/{workflow_id}
```

Get a specific workflow by ID.

**Response:**
```json
{
  "id": "workflow-123",
  "name": "Document Processing",
  "description": "Process and index documents",
  "domain_id": "domain-456",
  "yaml_definition": { "version": "1.0", "steps": [] },
  "is_active": true,
  "created_at": "2024-10-18T10:30:00Z"
}
```

#### Create Workflow
```
POST /api/v1/workflows
Status: 201 Created
```

Create a new workflow.

**Request Body:**
```json
{
  "name": "Document Processing",
  "description": "Process and index documents",
  "domain_id": "domain-456",
  "yaml_definition": {
    "version": "1.0",
    "actors": [],
    "activities": []
  },
  "is_active": true
}
```

**Response:**
```json
{
  "id": "workflow-123",
  "name": "Document Processing",
  "domain_id": "domain-456",
  "is_active": true,
  "created_at": "2024-10-18T10:30:00Z"
}
```

#### Update Workflow
```
PUT /api/v1/workflows/{workflow_id}
```

Update an existing workflow.

**Request Body:**
```json
{
  "name": "Updated Workflow Name",
  "description": "Updated description",
  "domain_id": "domain-456",
  "yaml_definition": { "version": "1.0" },
  "is_active": true
}
```

#### Delete Workflow
```
DELETE /api/v1/workflows/{workflow_id}
Status: 204 No Content
```

Delete a workflow.

---

### Document Management

#### List Documents
```
GET /api/v1/documents
GET /api/v1/documents?domain_id={domain_id}
```

List all documents or filter by domain.

**Query Parameters:**
- `domain_id` (optional) - Filter by domain UUID

**Response:**
```json
{
  "documents": [
    {
      "id": "doc-123",
      "name": "Architecture Guide",
      "domain_id": "domain-456",
      "file_path": "domain-456/docs/architecture.pdf",
      "file_type": "application/pdf",
      "size_bytes": 1024000,
      "status": "indexed",
      "created_at": "2024-10-18T10:00:00Z"
    }
  ],
  "count": 1
}
```

#### Get Document
```
GET /api/v1/documents/{document_id}
```

Get a specific document by ID.

**Response:**
```json
{
  "id": "doc-123",
  "name": "Architecture Guide",
  "domain_id": "domain-456",
  "file_path": "domain-456/docs/architecture.pdf",
  "file_type": "application/pdf",
  "size_bytes": 1024000,
  "status": "indexed",
  "created_at": "2024-10-18T10:00:00Z"
}
```

#### Create Document
```
POST /api/v1/documents
Status: 201 Created
```

Create a new document reference.

**Request Body:**
```json
{
  "name": "Architecture Guide",
  "domain_id": "domain-456",
  "file_path": "domain-456/docs/architecture.pdf",
  "file_type": "application/pdf",
  "size_bytes": 1024000
}
```

**Response:**
```json
{
  "id": "doc-123",
  "name": "Architecture Guide",
  "domain_id": "domain-456",
  "status": "pending",
  "created_at": "2024-10-18T10:00:00Z"
}
```

#### Delete Document
```
DELETE /api/v1/documents/{document_id}
Status: 204 No Content
```

Delete a document.

---

### Domain Management

#### List Domains
```
GET /api/v1/domains
```

List all domains.

**Response:**
```json
{
  "domains": [
    {
      "id": "domain-456",
      "name": "Engineering",
      "description": "Engineering knowledge base",
      "created_at": "2024-10-15T08:00:00Z",
      "created_by": "user-123"
    }
  ],
  "count": 1
}
```

#### Get Domain
```
GET /api/v1/domains/{domain_id}
```

Get a specific domain by ID.

**Response:**
```json
{
  "id": "domain-456",
  "name": "Engineering",
  "description": "Engineering knowledge base",
  "created_at": "2024-10-15T08:00:00Z",
  "created_by": "user-123"
}
```

#### Create Domain
```
POST /api/v1/domains
Status: 201 Created
```

Create a new domain and index it in Weaviate and Neo4j.

**Request Body:**
```json
{
  "domain_id": "domain-456",
  "name": "Engineering",
  "description": "Engineering knowledge base",
  "created_by": "user-123"
}
```

**Response:**
```json
{
  "domain_id": "domain-456",
  "status": "indexed",
  "message": "Domain created and indexed successfully"
}
```

#### Search Domains
```
GET /api/v1/domains/search
GET /api/v1/domains/search?q={query}&user_id={user_id}&use_llm={true|false}
```

Semantic search across domains using Weaviate + Neo4j + LLM.

**Query Parameters:**
- `q` (required) - Search query
- `user_id` (optional) - User ID for personalized results
- `use_llm` (optional, default: true) - Whether to use LLM to summarize results

**Response:**
```json
{
  "query": "machine learning platform",
  "results": {
    "vector_results": [
      {
        "domain_id": "domain-456",
        "name": "ML Platform",
        "description": "Machine learning infrastructure",
        "created_by": "user-123"
      }
    ],
    "graph_results": [
      {
        "domain_id": "domain-789",
        "name": "Data Science",
        "description": "Data science tools",
        "creator_name": "Jane Doe",
        "is_member": true
      }
    ]
  },
  "summary": "Based on your query, the ML Platform domain seems most relevant...",
  "result_count": {
    "vector": 1,
    "graph": 1
  }
}
```

---

### Workflow Results

#### Get Workflow Results
```
GET /api/v1/workflows/{workflow_id}/results
```

Get the final results of a completed workflow.

**Response:**
```json
{
  "workflow_id": "doc-123",
  "results": {
    "status": "completed",
    "documents_indexed": 1,
    "embeddings_generated": 1,
    "neo4j_updated": true,
    "completed_at": "2024-10-18T10:45:00Z"
  }
}
```

Or if still processing:
```json
{
  "workflow_id": "doc-123",
  "results": null,
  "message": "Workflow is still processing or no results available"
}
```

---

## Error Responses

All endpoints return standard HTTP error codes:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found: workflow-123"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to process request: [error message]"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Temporal client not initialized"
}
```

---

## Summary

| Endpoint | Method | Purpose | Async |
|----------|--------|---------|-------|
| `/health` | GET | Health check | No |
| `/api/v1/documents` | POST | Upload & process document | **Yes** |
| `/api/v1/questions` | POST | Ask question | **Yes** |
| `/api/v1/reviews` | POST | Submit review | **Yes** |
| `/api/v1/workflows/{id}` | GET | Get workflow status | No |
| `/api/v1/workflows/{id}/results` | GET | Get workflow results | No |
| `/api/v1/workflows` | GET | List workflows | No |
| `/api/v1/workflows` | POST | Create workflow | No |
| `/api/v1/workflows/{id}` | PUT | Update workflow | No |
| `/api/v1/workflows/{id}` | DELETE | Delete workflow | No |
| `/api/v1/documents` | GET | List documents | No |
| `/api/v1/documents/{id}` | GET | Get document | No |
| `/api/v1/documents` | POST | Create document | No |
| `/api/v1/documents/{id}` | DELETE | Delete document | No |
| `/api/v1/domains` | GET | List domains | No |
| `/api/v1/domains/{id}` | GET | Get domain | No |
| `/api/v1/domains` | POST | Create domain | No |
| `/api/v1/domains/search` | GET | Search domains | No |

---

## Implementation Notes

### Async Workflows (202 Accepted)

Endpoints marked "Async" return immediately with a `workflow_id`. Use the `/api/v1/workflows/{workflow_id}` endpoint to poll for status.

### Supabase Integration

- All data is stored in Supabase (PostgreSQL + Auth)
- Frontend can read/write Supabase directly via RLS policies
- Backend uses Supabase client for server-side operations
- Workflows update Supabase after completion

### Internal Systems

- **Temporal:** Orchestrates long-running workflows
- **Neo4j:** Knowledge graph for document relationships
- **Weaviate:** Vector database for semantic search

These are never accessed directly by frontend - only through FastAPI endpoints.

---

## Deployment

See `DEPLOYMENT.md` in the backend directory for deployment instructions.

# Backend API Reference

Complete reference for Hey.sh REST API endpoints, authentication, and integration.

## Authentication

### Overview

All API endpoints require authentication using Supabase JWT tokens. The frontend obtains a JWT token after user login/signup and includes it in the `Authorization` header of all API requests.

### JWT Flow

```
User Login
    ↓
Supabase Auth → JWT Token
    ↓
Frontend stores JWT (localStorage)
    ↓
Frontend includes JWT in Authorization header
    ↓
Backend validates JWT with Supabase public key
    ↓
Protected endpoint returns data or 401 Unauthorized
```

### Implementation

All API routes are protected with the `verify_jwt()` dependency:

```python
from fastapi import Depends
from backend.service.auth import verify_jwt

@router.get("/api/v1/documents")
async def list_documents(
    current_user: dict = Depends(verify_jwt)
):
    # current_user contains:
    # - id: user UUID
    # - email: user email
    # - role: user role
    # - app_metadata: application-specific data
    # - user_metadata: user-provided metadata
    pass
```

### Error Responses

```json
{
  "detail": "Invalid authentication credentials"
}
```

**Status Code**: 401 Unauthorized

## API Endpoints

### Base URL
- **Local**: http://api.hey.local (via Caddy)
- **Direct**: http://localhost:8000
- **Docs**: http://api.hey.local/docs (interactive Swagger UI)

### Health Check

**GET** `/health`

Check API server health.

**Response** (200):
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

### Authentication Endpoints

#### Verify Token

**GET** `/api/v1/auth/verify`

Verify current JWT token and get user info.

**Headers**:
```
Authorization: Bearer {jwt_token}
```

**Response** (200):
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "role": "user",
  "app_metadata": {},
  "user_metadata": {}
}
```

---

### Workflow Endpoints

#### Create Workflow

**POST** `/api/v1/workflows`

Start a new workflow execution.

**Headers**:
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Body**:
```json
{
  "workflow_type": "DocumentProcessingWorkflow",
  "input_data": {
    "document_id": "doc-123",
    "domain": "legal"
  }
}
```

**Response** (202 Accepted):
```json
{
  "workflow_id": "workflow-uuid",
  "status": "RUNNING",
  "created_at": "2025-10-21T10:00:00Z"
}
```

#### List Workflows

**GET** `/api/v1/workflows`

List all workflows for current user.

**Query Parameters**:
- `limit`: Number of results (default: 10)
- `offset`: Pagination offset (default: 0)
- `status`: Filter by status (RUNNING, COMPLETED, FAILED)

**Response** (200):
```json
{
  "workflows": [
    {
      "workflow_id": "workflow-uuid",
      "workflow_type": "DocumentProcessingWorkflow",
      "status": "COMPLETED",
      "created_at": "2025-10-21T10:00:00Z",
      "updated_at": "2025-10-21T10:05:00Z"
    }
  ],
  "total": 42,
  "limit": 10,
  "offset": 0
}
```

#### Get Workflow

**GET** `/api/v1/workflows/{workflow_id}`

Get details of a specific workflow.

**Response** (200):
```json
{
  "workflow_id": "workflow-uuid",
  "workflow_type": "DocumentProcessingWorkflow",
  "status": "COMPLETED",
  "created_at": "2025-10-21T10:00:00Z",
  "updated_at": "2025-10-21T10:05:00Z",
  "input_data": {
    "document_id": "doc-123"
  }
}
```

#### Get Workflow Results

**GET** `/api/v1/workflows/{workflow_id}/status`

Get the execution status and results of a workflow.

**Response** (200):
```json
{
  "workflow_id": "workflow-uuid",
  "status": "COMPLETED",
  "result": {
    "processed_pages": 42,
    "extracted_entities": 156,
    "vector_id": "vector-xyz"
  },
  "error": null
}
```

---

### Document Endpoints

#### Create Document

**POST** `/api/v1/documents`

Create a new document reference and start processing workflow.

**Headers**:
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Body**:
```json
{
  "filename": "contract.pdf",
  "content_type": "application/pdf",
  "supabase_path": "documents/user-123/contract.pdf",
  "domain": "legal"
}
```

**Response** (202 Accepted):
```json
{
  "document_id": "doc-uuid",
  "workflow_id": "workflow-uuid",
  "status": "PROCESSING",
  "created_at": "2025-10-21T10:00:00Z"
}
```

#### List Documents

**GET** `/api/v1/documents`

List all documents for current user.

**Query Parameters**:
- `limit`: Number of results (default: 10)
- `offset`: Pagination offset (default: 0)
- `domain`: Filter by domain

**Response** (200):
```json
{
  "documents": [
    {
      "document_id": "doc-uuid",
      "filename": "contract.pdf",
      "domain": "legal",
      "status": "INDEXED",
      "created_at": "2025-10-21T10:00:00Z",
      "updated_at": "2025-10-21T10:05:00Z"
    }
  ],
  "total": 25,
  "limit": 10,
  "offset": 0
}
```

#### Get Document

**GET** `/api/v1/documents/{document_id}`

Get details of a specific document.

**Response** (200):
```json
{
  "document_id": "doc-uuid",
  "filename": "contract.pdf",
  "domain": "legal",
  "status": "INDEXED",
  "content_preview": "Lorem ipsum dolor sit amet...",
  "created_at": "2025-10-21T10:00:00Z",
  "updated_at": "2025-10-21T10:05:00Z"
}
```

#### Delete Document

**DELETE** `/api/v1/documents/{document_id}`

Delete a document and remove from all indexes.

**Response** (204 No Content)

---

### Domain Endpoints

#### Create Domain

**POST** `/api/v1/domains`

Create a new knowledge domain and index it.

**Headers**:
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Body**:
```json
{
  "name": "Contract Law",
  "description": "Legal contracts and agreements",
  "metadata": {
    "industry": "legal"
  }
}
```

**Response** (201 Created):
```json
{
  "domain_id": "domain-uuid",
  "name": "Contract Law",
  "description": "Legal contracts and agreements",
  "created_at": "2025-10-21T10:00:00Z"
}
```

#### List Domains

**GET** `/api/v1/domains`

List all domains accessible to current user.

**Query Parameters**:
- `limit`: Number of results (default: 10)
- `offset`: Pagination offset (default: 0)

**Response** (200):
```json
{
  "domains": [
    {
      "domain_id": "domain-uuid",
      "name": "Contract Law",
      "description": "Legal contracts and agreements",
      "document_count": 42,
      "created_at": "2025-10-21T10:00:00Z"
    }
  ],
  "total": 5,
  "limit": 10,
  "offset": 0
}
```

#### Get Domain

**GET** `/api/v1/domains/{domain_id}`

Get details of a specific domain.

**Response** (200):
```json
{
  "domain_id": "domain-uuid",
  "name": "Contract Law",
  "description": "Legal contracts and agreements",
  "document_count": 42,
  "created_at": "2025-10-21T10:00:00Z"
}
```

#### Search Domain

**GET** `/api/v1/domains/{domain_id}/search`

Semantic search within a domain.

**Query Parameters**:
- `query`: Search query (required)
- `limit`: Number of results (default: 10)

**Response** (200):
```json
{
  "results": [
    {
      "document_id": "doc-xyz",
      "filename": "contract.pdf",
      "relevance_score": 0.95,
      "excerpt": "The parties agree to the following terms..."
    }
  ],
  "total_results": 127,
  "query_time_ms": 234
}
```

---

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid request body"
}
```

### 401 Unauthorized

```json
{
  "detail": "Invalid authentication credentials"
}
```

### 403 Forbidden

```json
{
  "detail": "You do not have permission to access this resource"
}
```

### 404 Not Found

```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error"
}
```

---

## Integration Examples

### JavaScript/TypeScript (Frontend)

```typescript
// Get JWT token from Supabase
const { data: { session } } = await supabase.auth.getSession();
const token = session?.access_token;

// Create headers with JWT
const headers = {
  "Authorization": `Bearer ${token}`,
  "Content-Type": "application/json"
};

// Create document and start processing
const response = await fetch("http://api.hey.local/api/v1/documents", {
  method: "POST",
  headers,
  body: JSON.stringify({
    filename: "contract.pdf",
    content_type: "application/pdf",
    supabase_path: "documents/user-123/contract.pdf",
    domain: "legal"
  })
});

const result = await response.json();
console.log("Workflow ID:", result.workflow_id);
```

### Python

```python
import requests
from supabase import create_client

# Get JWT token from Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

response = supabase.auth.sign_in_with_password({
  "email": "user@example.com",
  "password": "password"
})
token = response.session.access_token

# Call API with JWT
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    "http://api.hey.local/api/v1/documents",
    headers=headers,
    json={
        "filename": "contract.pdf",
        "content_type": "application/pdf",
        "supabase_path": "documents/user-123/contract.pdf",
        "domain": "legal"
    }
)
print(response.json())
```

### cURL

```bash
# Get JWT token (example)
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Create document
curl -X POST http://api.hey.local/api/v1/documents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "contract.pdf",
    "content_type": "application/pdf",
    "supabase_path": "documents/user-123/contract.pdf",
    "domain": "legal"
  }'
```

---

## Rate Limiting

API requests are rate limited:
- **Authenticated users**: 1000 requests per minute
- **Anonymous**: 100 requests per minute

**Rate limit headers**:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1634836800
```

---

## Versioning

The API uses URL versioning (`/api/v1/`). Future versions will be available at `/api/v2/`, etc.

**Current version**: v1

---

## Support

- **Interactive Docs**: http://api.hey.local/docs
- **Logs**: Check `docker-compose logs -f api`
- **Issues**: Review [../README.md](../README.md) troubleshooting section

---

**Last Updated**: October 21, 2025
**Status**: Production Ready
**Version**: 1.0

# Hey.sh API Documentation

## 🌐 Base URLs

### **Development**
- **HTTP**: `http://api.hey.local`
- **HTTPS**: `https://api.hey.local`

### **Production**
- **HTTPS**: `https://api.hey.sh`

## 🔐 Authentication

All API endpoints require JWT authentication via the `Authorization` header:

```bash
Authorization: Bearer <jwt_token>
```

## 📋 API Endpoints

### **Health & Info**

#### **GET /health**
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

#### **GET /api/v1/info**
Backend version and environment information.

**Response:**
```json
{
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

### **Documents**

#### **POST /api/v1/documents**
Upload a document and trigger processing workflow.

**Request:**
```json
{
  "file": "<file_data>",
  "domain_id": "uuid",
  "metadata": {
    "title": "Document Title",
    "description": "Document description"
  }
}
```

**Response:**
```json
{
  "document_id": "uuid",
  "workflow_id": "uuid",
  "status": "processing",
  "message": "Document uploaded successfully"
}
```

#### **GET /api/v1/documents**
List documents for a domain.

**Query Parameters:**
- `domain_id` (required): Domain UUID

**Response:**
```json
{
  "documents": [
    {
      "id": "uuid",
      "title": "Document Title",
      "status": "processed",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### **GET /api/v1/documents/{documentId}**
Get specific document details.

**Response:**
```json
{
  "id": "uuid",
  "title": "Document Title",
  "content": "Document content",
  "status": "processed",
  "metadata": {},
  "created_at": "2025-01-01T00:00:00Z"
}
```

### **Questions**

#### **POST /api/v1/questions**
Ask a question and trigger Q&A workflow.

**Request:**
```json
{
  "question": "What is the main topic?",
  "domain_id": "uuid",
  "context": "Additional context"
}
```

**Response:**
```json
{
  "question_id": "uuid",
  "workflow_id": "uuid",
  "status": "processing",
  "message": "Question submitted successfully"
}
```

### **Reviews**

#### **POST /api/v1/reviews**
Submit a review and trigger review workflow.

**Request:**
```json
{
  "content": "Review content",
  "rating": 5,
  "domain_id": "uuid",
  "user_id": "uuid"
}
```

**Response:**
```json
{
  "review_id": "uuid",
  "workflow_id": "uuid",
  "status": "processing",
  "message": "Review submitted successfully"
}
```

### **Workflows**

#### **GET /api/v1/workflows**
List workflows for a domain.

**Query Parameters:**
- `domain_id` (required): Domain UUID

**Response:**
```json
{
  "workflows": [
    {
      "id": "uuid",
      "type": "document_processing",
      "status": "running",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### **GET /api/v1/workflows/{workflowId}**
Get workflow status.

**Response:**
```json
{
  "id": "uuid",
  "type": "document_processing",
  "status": "running",
  "progress": 75,
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### **GET /api/v1/workflows/{workflowId}/results**
Get workflow results.

**Response:**
```json
{
  "id": "uuid",
  "status": "completed",
  "results": {
    "summary": "Processing complete",
    "data": {}
  },
  "completed_at": "2025-01-01T00:00:00Z"
}
```

### **Domains**

#### **POST /api/v1/domains**
Create a new domain.

**Request:**
```json
{
  "name": "Domain Name",
  "description": "Domain description",
  "owner_id": "uuid"
}
```

**Response:**
```json
{
  "domain_id": "uuid",
  "name": "Domain Name",
  "status": "active",
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### **GET /api/v1/domains**
List all domains.

**Response:**
```json
{
  "domains": [
    {
      "id": "uuid",
      "name": "Domain Name",
      "status": "active",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### **GET /api/v1/domains/{domainId}**
Get specific domain details.

**Response:**
```json
{
  "id": "uuid",
  "name": "Domain Name",
  "description": "Domain description",
  "status": "active",
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### **GET /api/v1/domains/search**
Semantic search across domains.

**Query Parameters:**
- `q` (required): Search query
- `user_id` (required): User UUID
- `use_llm` (optional): Boolean, default false

**Response:**
```json
{
  "results": [
    {
      "id": "uuid",
      "name": "Domain Name",
      "relevance_score": 0.95,
      "snippet": "Relevant content snippet"
    }
  ]
}
```

### **Users**

#### **GET /api/v1/users/{userId}/profile**
Get user profile.

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "User Name",
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### **GET /api/v1/users/{userId}/domains**
Get domains owned by or where user is a member.

**Response:**
```json
{
  "domains": [
    {
      "id": "uuid",
      "name": "Domain Name",
      "role": "owner",
      "joined_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### **GET /api/v1/users/{userId}/membership-requests**
Get user's membership requests.

**Response:**
```json
{
  "requests": [
    {
      "id": "uuid",
      "domain_id": "uuid",
      "domain_name": "Domain Name",
      "status": "pending",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

### **Membership**

#### **POST /api/v1/membership-requests**
Create a membership request.

**Request:**
```json
{
  "domain_id": "uuid",
  "user_id": "uuid",
  "message": "Request message"
}
```

**Response:**
```json
{
  "request_id": "uuid",
  "status": "pending",
  "message": "Membership request created successfully"
}
```

### **WebSocket**

#### **WebSocket /ws**
Real-time workflow signals and updates.

**Connection:**
```javascript
const ws = new WebSocket('wss://api.hey.local/ws');
```

**Authentication:**
```javascript
ws.send(JSON.stringify({
  type: 'auth',
  token: 'jwt_token'
}));
```

**Message Types:**
- `status_update`: Workflow status updates
- `completion`: Workflow completion
- `error`: Workflow errors
- `progress`: Progress updates

**Example Message:**
```json
{
  "type": "status_update",
  "workflow_id": "uuid",
  "status": "running",
  "progress": 50,
  "message": "Processing document..."
}
```

### **GraphQL**

#### **POST /api/v1/graphql**
Generic GraphQL endpoint.

**Request:**
```json
{
  "query": "query { domains { id name } }",
  "variables": {}
}
```

**Response:**
```json
{
  "data": {
    "domains": [
      {
        "id": "uuid",
        "name": "Domain Name"
      }
    ]
  }
}
```

## 🔧 Configuration

### **Frontend Configuration**

#### **GET /api/v1/config/frontend**
Get frontend configuration (JSON).

**Response:**
```json
{
  "supabase": {
    "url": "https://supabase.hey.local",
    "anon_key": "local-development-key"
  },
  "api": {
    "url": "https://api.hey.local"
  },
  "temporal": {
    "address": "https://temporal.hey.local",
    "namespace": "default"
  },
  "environment": "development"
}
```

#### **GET /api/v1/config/frontend.js**
Get frontend configuration (JavaScript).

**Response:**
```javascript
window.HEY_CONFIG = {
  VITE_SUPABASE_URL: "https://supabase.hey.local",
  VITE_SUPABASE_ANON_KEY: "local-development-key",
  VITE_API_URL: "https://api.hey.local",
  VITE_TEMPORAL_ADDRESS: "https://temporal.hey.local",
  VITE_TEMPORAL_NAMESPACE: "default",
  NODE_ENV: "development"
};
```

## 🚨 Error Handling

### **Error Response Format**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    }
  }
}
```

### **HTTP Status Codes**
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

## 🔄 Rate Limiting

- **API Endpoints**: 100 requests per minute per user
- **WebSocket**: 10 connections per user
- **File Upload**: 10MB per request, 100MB per hour

## 📝 Examples

### **Complete Document Processing Flow**
```bash
# 1. Upload document
curl -X POST https://api.hey.local/api/v1/documents \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.pdf" \
  -F "domain_id=uuid"

# 2. Check workflow status
curl -X GET https://api.hey.local/api/v1/workflows/{workflow_id} \
  -H "Authorization: Bearer <token>"

# 3. Get results
curl -X GET https://api.hey.local/api/v1/workflows/{workflow_id}/results \
  -H "Authorization: Bearer <token>"
```

### **WebSocket Connection**
```javascript
const ws = new WebSocket('wss://api.hey.local/ws');

ws.onopen = () => {
  // Authenticate
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'jwt_token'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

---

This API provides a comprehensive interface for the Hey.sh knowledge management platform with real-time updates and flexible querying capabilities.
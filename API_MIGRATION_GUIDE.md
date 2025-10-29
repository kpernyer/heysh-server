# API Migration Guide: Domain → Topic

## Overview

This guide documents the API changes resulting from renaming "Domain" to "Topic" throughout the backend. All API endpoints, request/response models, and field names have been updated to reflect this change.

## Breaking Changes Summary

### Terminology Changes
- **Domain** → **Topic**
- **domain_id** → **topic_id**
- **domains** table → **topics** table (database migration required)

### Endpoint Changes

| Old Endpoint | New Endpoint | Method | Description |
|-------------|-------------|--------|-------------|
| `GET /api/v1/domains` | `GET /api/v1/topics` | GET | List all topics |
| `GET /api/v1/domains/search` | `GET /api/v1/topics/search` | GET | Search topics |
| `GET /api/v1/domains/{domain_id}` | `GET /api/v1/topics/{topic_id}` | GET | Get specific topic |
| `POST /api/v1/domains` | `POST /api/v1/topics` | POST | Create new topic |

### Request Field Changes

All requests that previously used `domain_id` now use `topic_id`:

- `UploadDocumentRequest`: `domain_id` → `topic_id`
- `AskQuestionRequest`: `domain_id` → `topic_id`
- `SubmitReviewRequest`: `domain_id` → `topic_id`
- `WorkflowDataRequest`: `domain_id` → `topic_id`
- `DocumentDataRequest`: `domain_id` → `topic_id`

## Updated API Endpoints

### 1. Health Check
**Endpoint:** `GET /health`
**Auth Required:** No
**Response:**
```json
{
  "status": "healthy"
}
```

### 2. Upload Document
**Endpoint:** `POST /api/v1/documents`
**Auth Required:** Yes (JWT)
**Request Body:**
```json
{
  "document_id": "doc-123",
  "topic_id": "topic-456",
  "file_path": "topic-456/document-123.pdf"
}
```
**Response:**
```json
{
  "workflow_id": "doc-123",
  "status": "processing",
  "message": "Document processing started"
}
```

### 3. Ask Question
**Endpoint:** `POST /api/v1/questions`
**Auth Required:** Yes (JWT)
**Request Body:**
```json
{
  "question_id": "q-123",
  "question": "What is the meaning of life?",
  "topic_id": "topic-456",
  "user_id": "user-789"
}
```
**Response:**
```json
{
  "workflow_id": "question-123",
  "status": "processing",
  "message": "Question answering started"
}
```

### 4. Get Workflow Status
**Endpoint:** `GET /api/v1/workflows/{workflow_id}/status`
**Auth Required:** No
**Response:**
```json
{
  "workflow_id": "doc-123",
  "status": "RUNNING",
  "type": "DocumentProcessingWorkflow"
}
```

### 5. Create Topic
**Endpoint:** `POST /api/v1/topics`
**Auth Required:** Yes (JWT)
**Request Body:**
```json
{
  "topic_id": "topic-123",
  "name": "Machine Learning",
  "description": "A topic about machine learning and AI",
  "created_by": "user-456"
}
```
**Response:**
```json
{
  "topic_id": "topic-123",
  "name": "Machine Learning",
  "description": "A topic about machine learning and AI",
  "created_by": "user-456",
  "status": "indexed",
  "message": "Topic created and indexed successfully"
}
```

### 6. Search Topics
**Endpoint:** `GET /api/v1/topics/search`
**Auth Required:** Yes (JWT)
**Query Parameters:**
- `q` (required): Search query string
- `user_id` (required): User ID performing the search
- `use_llm` (optional, default: true): Whether to use LLM for summarization

**Example:** `GET /api/v1/topics/search?q=machine learning&user_id=user-123&use_llm=true`

**Response:**
```json
{
  "query": "machine learning",
  "results": {
    "vector_results": [
      {
        "name": "ML Basics",
        "description": "Introduction to machine learning"
      }
    ],
    "graph_results": [
      {
        "name": "Deep Learning",
        "description": "Advanced ML techniques",
        "is_member": true
      }
    ]
  },
  "summary": "Based on your search, here are the most relevant topics...",
  "result_count": {
    "vector": 5,
    "graph": 3
  }
}
```

### 7. List Topics
**Endpoint:** `GET /api/v1/topics`
**Auth Required:** Yes (JWT)
**Response:**
```json
{
  "topics": [
    {
      "id": "topic-123",
      "name": "Machine Learning",
      "description": "ML topic",
      "created_by": "user-456",
      "created_at": "2025-01-15T10:00:00Z"
    }
  ],
  "count": 1
}
```

### 8. Get Topic by ID
**Endpoint:** `GET /api/v1/topics/{topic_id}`
**Auth Required:** Yes (JWT)
**Response:**
```json
{
  "id": "topic-123",
  "name": "Machine Learning",
  "description": "ML topic",
  "created_by": "user-456",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

## Frontend Migration Checklist

### Required Changes in Frontend Code

1. **Update API Client** (`backend-api.ts` or similar):
   - [ ] Change `createDomain()` to `createTopic()`
   - [ ] Change `searchDomains()` to `searchTopics()`
   - [ ] Change `domain_id` parameter to `topic_id` in all API calls
   - [ ] Update endpoint URLs: `/domains` → `/topics`

2. **Update Request Interfaces:**
```typescript
// OLD
interface UploadDocumentRequest {
  document_id: string;
  domain_id: string;  // ❌ CHANGE THIS
  file_path: string;
}

// NEW
interface UploadDocumentRequest {
  document_id: string;
  topic_id: string;   // ✅ USE THIS
  file_path: string;
}
```

3. **Update API Function Calls:**
```typescript
// OLD
const result = await uploadDocument(
  "doc-123",
  "domain-456",  // ❌
  "path/to/file.pdf",
  "file.pdf"
);

// NEW
const result = await uploadDocument(
  "doc-123",
  "topic-456",   // ✅
  "path/to/file.pdf",
  "file.pdf"
);
```

4. **Update Create Domain/Topic Calls:**
```typescript
// OLD
const result = await createDomain({
  domain_id: "domain-123",  // ❌
  name: "ML Topics",
  description: "Machine learning",
  created_by: "user-456"
});

// NEW
const result = await createTopic({
  topic_id: "topic-123",    // ✅
  name: "ML Topics",
  description: "Machine learning",
  created_by: "user-456"
});
```

5. **Update Search Calls:**
```typescript
// OLD
const result = await searchDomains("machine learning", "user-123", true);

// NEW
const result = await searchTopics("machine learning", "user-123", true);
```

## Database Migration Required

The backend expects the following database changes:

1. Rename table: `domains` → `topics`
2. Update foreign key references in related tables:
   - `documents.domain_id` → `documents.topic_id`
   - `workflows.domain_id` → `workflows.topic_id`
   - `domain_members` → `topic_members`
   - `domain_members.domain_id` → `topic_members.topic_id`

## Role Terminology Updates

The `TopicRole` enum now includes all HITL workflow roles:
- `OWNER` - Full control over the topic
- `CONTRIBUTOR` - Can add/edit content
- `CONTROLLER` - Can review and approve changes
- `MEMBER` - Read access only

## Notes

1. **Workflows are internal**: The frontend doesn't need to understand workflow internals. The API abstracts workflows away and only returns `workflow_id` for status tracking.

2. **Backward Compatibility**: There is NO backward compatibility for domain terminology. All frontend code must be updated to use topic terminology.

3. **Authentication**: Most endpoints require a valid JWT token in the `Authorization` header: `Authorization: Bearer <token>`

4. **Error Handling**: All endpoints return standard HTTP status codes:
   - `200/201` - Success
   - `400` - Bad Request
   - `401` - Unauthorized
   - `404` - Not Found
   - `500` - Internal Server Error

## Testing

Update the frontend test file to use the new terminology:

```typescript
// OLD test names
const testCreateDomain = async () => { /* ... */ }
const testSearchDomains = async () => { /* ... */ }

// NEW test names
const testCreateTopic = async () => { /* ... */ }
const testSearchTopics = async () => { /* ... */ }
```

## Questions or Issues?

If you encounter any issues during migration, please check:
1. All `domain_id` fields have been changed to `topic_id`
2. All endpoint URLs use `/topics` instead of `/domains`
3. Function names have been updated (`createTopic`, `searchTopics`, etc.)
4. The database migration has been applied

For additional support, refer to the API documentation at `/api/v1/info` or contact the backend team.

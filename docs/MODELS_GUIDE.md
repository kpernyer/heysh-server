# Data Models Guide

Complete guide to using the data models for Supabase operations in the backend.

## Overview

The data models provide a structured layer for all Supabase database operations. This ensures:

- **Consistency:** All database operations go through defined methods
- **Type Safety:** Strong typing with proper error handling
- **Testability:** Easy to mock and test
- **Reusability:** Models used by APIs, workflows, and activities
- **Logging:** All operations logged for debugging

## Architecture

```
┌────────────────────────┐
│   FastAPI Routes       │  (backend/service/routes_data.py)
└───────────┬────────────┘
            │ uses
┌───────────▼────────────┐
│   Data Models          │  (backend/service/models/)
│ • DocumentModel        │
│ • WorkflowModel        │
│ • DomainModel          │
│ • ReviewModel          │
└───────────┬────────────┘
            │ uses
┌───────────▼────────────┐
│   BaseModel            │  (common CRUD operations)
└───────────┬────────────┘
            │ uses
┌───────────▼────────────┐
│   Supabase Client      │
└────────────────────────┘
```

## Models

### BaseModel

Base class with common CRUD operations used by all models.

**Methods:**

```python
@classmethod
async def get_by_id(cls, item_id: str) -> Optional[dict]
    """Get single item by ID"""

@classmethod
async def list_all(cls, filters: Optional[dict]) -> list[dict]
    """List all items, optionally filtered"""

@classmethod
async def create(cls, data: dict) -> dict
    """Create new item"""

@classmethod
async def update(cls, item_id: str, data: dict) -> dict
    """Update existing item"""

@classmethod
async def delete(cls, item_id: str) -> bool
    """Delete item, returns True if successful"""
```

**Example:**

```python
from service.models import DocumentModel

# Get by ID
doc = await DocumentModel.get_by_id("doc-123")

# List all
all_docs = await DocumentModel.list_all()

# List filtered
domain_docs = await DocumentModel.list_all({"domain_id": "domain-456"})

# Create
new_doc = await DocumentModel.create({
    "name": "Architecture Guide",
    "domain_id": "domain-456",
    "status": "pending"
})

# Update
updated = await DocumentModel.update("doc-123", {"status": "indexed"})

# Delete
success = await DocumentModel.delete("doc-123")
```

---

### DocumentModel

Manages document records and their processing status.

**Special Methods:**

```python
@classmethod
async def create_document(
    cls,
    name: str,
    domain_id: str,
    file_path: str,
    file_type: Optional[str] = None,
    size_bytes: Optional[int] = None,
    created_by: Optional[str] = None,
) -> dict
    """Create document with default status='pending'"""

@classmethod
async def update_status(
    cls,
    document_id: str,
    status: str,
    metadata: Optional[dict] = None,
) -> dict
    """Update document status and optionally add metadata"""

@classmethod
async def get_by_domain(cls, domain_id: str) -> list[dict]
    """Get all documents in a domain"""

@classmethod
async def get_by_status(cls, status: str) -> list[dict]
    """Get documents with specific status"""

@classmethod
async def add_metadata(
    cls,
    document_id: str,
    metadata_key: str,
    metadata_value: Any,
) -> dict
    """Add or update metadata for document"""

@classmethod
async def record_processing_error(
    cls,
    document_id: str,
    error_message: str,
) -> dict
    """Record processing failure"""

@classmethod
async def record_processing_success(
    cls,
    document_id: str,
    weaviate_id: Optional[str] = None,
    neo4j_updated: bool = False,
    embeddings_count: Optional[int] = None,
) -> dict
    """Record successful processing"""
```

**Typical Flow:**

```python
# 1. Create document
doc = await DocumentModel.create_document(
    name="document.pdf",
    domain_id="domain-123",
    file_path="domain-123/document.pdf"
)

# 2. Update status during processing
await DocumentModel.update_status(doc["id"], "processing")

# 3. Record success
await DocumentModel.record_processing_success(
    doc["id"],
    weaviate_id="vec-123",
    neo4j_updated=True,
    embeddings_count=150
)

# OR record error
await DocumentModel.record_processing_error(
    doc["id"],
    "Failed to extract text: [error details]"
)
```

**Status Values:**

- `pending` - Waiting to be processed
- `processing` - Currently being processed
- `indexed` - Successfully processed and indexed
- `failed` - Processing failed

---

### WorkflowModel

Manages workflow definitions and their executions.

**Special Methods:**

```python
@classmethod
async def create_workflow(
    cls,
    name: str,
    domain_id: str,
    yaml_definition: dict,
    description: Optional[str] = None,
    created_by: Optional[str] = None,
) -> dict
    """Create workflow definition"""

@classmethod
async def get_by_domain(cls, domain_id: str) -> list[dict]
    """Get all workflows in domain"""

@classmethod
async def get_active_workflows(cls) -> list[dict]
    """Get only active workflows"""

@classmethod
async def toggle_active(
    cls,
    workflow_id: str,
    is_active: bool,
) -> dict
    """Enable/disable workflow"""

@classmethod
async def record_execution(
    cls,
    workflow_id: str,
    execution_data: dict,
) -> Optional[str]
    """Record a workflow execution (returns execution ID)"""

@classmethod
async def get_execution_history(
    cls,
    workflow_id: str,
    limit: int = 10,
) -> list[dict]
    """Get recent executions"""

@classmethod
async def get_execution_stats(cls, workflow_id: str) -> dict
    """Get aggregated execution statistics"""
```

**Typical Flow:**

```python
# 1. Create workflow
workflow = await WorkflowModel.create_workflow(
    name="Document Processing",
    domain_id="domain-123",
    yaml_definition={...}
)

# 2. In your Temporal workflow, record execution
execution_id = await WorkflowModel.record_execution(
    workflow_id="temp-workflow-id",
    execution_data={
        "status": "completed",
        "duration_ms": 5000,
        "result": {"processed": 10},
        "started_at": start_time.isoformat()
    }
)

# 3. Get execution history
history = await WorkflowModel.get_execution_history(workflow["id"])

# 4. Get statistics
stats = await WorkflowModel.get_execution_stats(workflow["id"])
# Returns: {
#     "total_executions": 50,
#     "successful_executions": 48,
#     "failed_executions": 2,
#     "success_rate": 96.0,
#     "average_duration_ms": 4500
# }
```

---

### DomainModel

Manages domain records and indexing metadata.

**Special Methods:**

```python
@classmethod
async def create_domain(
    cls,
    name: str,
    description: Optional[str] = None,
    created_by: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict
    """Create domain"""

@classmethod
async def record_indexing(
    cls,
    domain_id: str,
    weaviate_indexed: bool = False,
    neo4j_indexed: bool = False,
) -> dict
    """Record that domain was indexed"""

@classmethod
async def get_user_domains(cls, user_id: str) -> list[dict]
    """Get domains created by user"""

@classmethod
async def update_stats(
    cls,
    domain_id: str,
    document_count: Optional[int] = None,
    member_count: Optional[int] = None,
) -> dict
    """Update domain statistics"""

@classmethod
async def record_indexing_error(
    cls,
    domain_id: str,
    error_message: str,
) -> dict
    """Record indexing failure"""

@classmethod
async def get_domains_needing_indexing(cls) -> list[dict]
    """Get domains not yet indexed"""
```

**Typical Flow:**

```python
# 1. Create domain
domain = await DomainModel.create_domain(
    name="Engineering",
    description="Engineering knowledge",
    created_by="user-123"
)

# 2. After indexing
await DomainModel.record_indexing(
    domain["id"],
    weaviate_indexed=True,
    neo4j_indexed=True
)

# 3. Update stats
await DomainModel.update_stats(
    domain["id"],
    document_count=15,
    member_count=5
)

# 4. Get domains needing indexing
pending = await DomainModel.get_domains_needing_indexing()
```

---

### ReviewModel

Manages review tasks and decisions.

**Special Methods:**

```python
@classmethod
async def create_review(
    cls,
    domain_id: str,
    reviewable_type: str,
    reviewable_id: str,
    reason: Optional[str] = None,
    created_by: Optional[str] = None,
) -> dict
    """Create review task"""

@classmethod
async def assign_to_reviewers(
    cls,
    review_id: str,
    reviewer_ids: list[str],
) -> dict
    """Assign to multiple reviewers"""

@classmethod
async def record_decision(
    cls,
    review_id: str,
    decision: str,  # approve, reject, changes_requested
    reviewer_id: str,
    comment: Optional[str] = None,
) -> dict
    """Record reviewer decision"""

@classmethod
async def get_pending_reviews(
    cls,
    domain_id: Optional[str] = None,
) -> list[dict]
    """Get pending reviews"""

@classmethod
async def get_reviews_for_reviewer(
    cls,
    reviewer_id: str,
) -> list[dict]
    """Get reviews assigned to reviewer"""

@classmethod
async def get_review_history(
    cls,
    reviewable_type: str,
    reviewable_id: str,
) -> list[dict]
    """Get all reviews for an item"""

@classmethod
async def get_domain_review_stats(cls, domain_id: str) -> dict
    """Get review statistics for domain"""

@classmethod
async def close_review(
    cls,
    review_id: str,
    final_decision: str,
) -> dict
    """Close review with final decision"""
```

**Typical Flow:**

```python
# 1. Create review
review = await ReviewModel.create_review(
    domain_id="domain-123",
    reviewable_type="document",
    reviewable_id="doc-456",
    reason="Low confidence score"
)

# 2. Assign reviewers
await ReviewModel.assign_to_reviewers(
    review["id"],
    ["user-admin-1", "user-controller-1"]
)

# 3. Record decisions
await ReviewModel.record_decision(
    review["id"],
    decision="approved",
    reviewer_id="user-admin-1",
    comment="Looks good"
)

# 4. Close review
await ReviewModel.close_review(
    review["id"],
    final_decision="approved"
)

# 5. Get stats
stats = await ReviewModel.get_domain_review_stats("domain-123")
# Returns: {
#     "total_reviews": 20,
#     "pending": 3,
#     "approved": 15,
#     "rejected": 2,
#     "approval_rate": 75.0,
#     "average_decision_time_seconds": 3600
# }
```

---

## Usage Patterns

### In FastAPI Routes

```python
from service.models import DocumentModel

@router.get("/documents")
async def list_documents(domain_id: str | None = None):
    if domain_id:
        docs = await DocumentModel.get_by_domain(domain_id)
    else:
        docs = await DocumentModel.list_all()

    return {"documents": docs, "count": len(docs)}

@router.post("/documents")
async def create_document(request: DocumentDataRequest):
    doc = await DocumentModel.create_document(
        name=request.name,
        domain_id=request.domain_id,
        file_path=request.file_path
    )
    return doc
```

### In Temporal Workflows

```python
from temporalio import workflow
from service.models import DocumentModel, WorkflowModel

@workflow.defn
class DocumentProcessingWorkflow:
    @workflow.run
    async def run(self, document_id: str, domain_id: str):
        # Update status
        await DocumentModel.update_status(document_id, "processing")

        # Do processing...
        result = await self._process()

        # Record success
        await DocumentModel.record_processing_success(
            document_id,
            weaviate_id=result["id"],
            neo4j_updated=True
        )

        # Record execution
        await WorkflowModel.record_execution(
            workflow.info().workflow_id,
            execution_data={
                "status": "completed",
                "result": result
            }
        )
```

### In Activities

```python
from temporalio import activity
from service.models import DocumentModel

@activity.defn
async def process_document_activity(document_id: str) -> dict:
    # Get document
    doc = await DocumentModel.get_by_id(document_id)

    # Do processing...

    # Update metadata
    await DocumentModel.add_metadata(
        document_id,
        "processed_at",
        datetime.utcnow().isoformat()
    )

    return {"status": "success"}
```

---

## Error Handling

All models raise exceptions for errors. Catch and handle appropriately:

```python
try:
    doc = await DocumentModel.get_by_id("invalid-id")
except Exception as e:
    logger.error(f"Failed to get document: {e}")
    # Handle error...
```

Models log all operations via structlog, so errors are automatically tracked.

---

## Best Practices

1. **Use specific model methods** - Don't call `BaseModel.update()` directly, use `DocumentModel.update_status()`
2. **Batch operations** - Use `list_all()` with filters instead of looping
3. **Store context in metadata** - Use metadata field for additional context
4. **Log important operations** - Models log automatically, but add context in your code
5. **Handle async properly** - Always `await` model calls
6. **Type hints** - Use type hints for all method parameters and returns
7. **Document workflows** - When using models in workflows, document the flow

---

## Summary

Data models provide a clean, structured way to interact with Supabase:

- **BaseModel:** Common CRUD operations
- **DocumentModel:** Document management and status tracking
- **WorkflowModel:** Workflow definitions and execution history
- **DomainModel:** Domain management and indexing tracking
- **ReviewModel:** Review task management and decisions

All models integrate seamlessly with FastAPI routes, Temporal workflows, and activities.

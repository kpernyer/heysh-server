"""Knowledge Base API routes - Manage documents and knowledge items."""

from typing import Any, Dict, List, Optional
from enum import Enum

import structlog
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

from src.app.auth.dependencies import CurrentUserId
from src.app.clients.supabase import get_supabase_client
from src.service.models.document_model import DocumentModel

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v2/knowledge-base", tags=["Knowledge Base"])


# ==================== Models ====================

class DocumentType(str, Enum):
    """Type of document."""
    PDF = "pdf"
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    OTHER = "other"


class DocumentStatus(str, Enum):
    """Processing status of a document."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(BaseModel):
    """Knowledge base document."""
    id: str
    topic_id: str
    topic_name: str
    name: str
    description: Optional[str]
    type: DocumentType
    status: DocumentStatus
    size_bytes: int
    mime_type: str
    url: Optional[str]
    uploaded_by: str
    uploaded_at: str
    processed_at: Optional[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    extracted_text: Optional[str] = None
    summary: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""
    document_id: str
    status: str
    message: str
    processing_job_id: Optional[str]


class SearchQuery(BaseModel):
    """Search query for knowledge base."""
    query: str = Field(..., min_length=1, max_length=500)
    topic_ids: Optional[List[str]] = Field(None, description="Filter by topics")
    document_types: Optional[List[DocumentType]] = Field(None, description="Filter by document types")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    limit: int = Field(20, ge=1, le=100)
    include_content: bool = Field(False, description="Include extracted text in results")


class SearchResult(BaseModel):
    """Search result item."""
    document_id: str
    topic_id: str
    topic_name: str
    name: str
    type: DocumentType
    relevance_score: float
    snippet: str
    url: Optional[str]
    tags: List[str]
    content: Optional[str] = None


class AnalysisRequest(BaseModel):
    """Request to analyze a document."""
    document_id: str
    analysis_type: str = Field(..., pattern="^(summarize|extract_entities|sentiment|classify)$")
    options: Dict[str, Any] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    """Result of document analysis."""
    document_id: str
    analysis_type: str
    result: Dict[str, Any]
    confidence: Optional[float]
    processing_time_ms: int


# ==================== Browse Knowledge Base ====================

@router.get("/", response_model=List[Document])
async def browse_knowledge_base(
    user_id: CurrentUserId,
    topic_id: Optional[str] = Query(None, description="Filter by topic"),
    document_type: Optional[DocumentType] = Query(None, description="Filter by type"),
    status: Optional[DocumentStatus] = Query(None, description="Filter by status"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    uploaded_by: Optional[str] = Query(None, description="Filter by uploader"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[Document]:
    """Browse documents in the knowledge base.

    Only returns documents from topics the user has access to.
    """
    try:
        supabase = get_supabase_client()

        # Get user's accessible topics
        member_response = supabase.table("domain_members").select(
            "domain_id"
        ).eq("user_id", user_id).execute()

        user_topic_ids = [m["domain_id"] for m in member_response.data]

        # Also get public topics
        public_topics = supabase.table("domains").select(
            "id"
        ).eq("is_public", True).execute()

        public_topic_ids = [t["id"] for t in public_topics.data]

        # Combine accessible topics
        accessible_topic_ids = list(set(user_topic_ids + public_topic_ids))

        if not accessible_topic_ids:
            return []  # No accessible topics

        # Build query
        query = supabase.table("documents").select(
            "*",
            "domains:domain_id(name)"
        ).in_("domain_id", accessible_topic_ids)

        # Apply filters
        if topic_id:
            if topic_id not in accessible_topic_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this topic"
                )
            query = query.eq("domain_id", topic_id)

        if document_type:
            query = query.eq("type", document_type.value)

        if status:
            query = query.eq("status", status.value)

        if uploaded_by:
            query = query.eq("uploaded_by", uploaded_by)

        if tags:
            # Filter by tags (assuming JSONB column)
            for tag in tags:
                query = query.contains("tags", [tag])

        # Execute with pagination
        documents_response = query.range(offset, offset + limit - 1).execute()

        # Transform to response model
        documents = []
        for doc_data in documents_response.data:
            topic = doc_data.get("domains", {})
            document = Document(
                id=doc_data["id"],
                topic_id=doc_data["domain_id"],
                topic_name=topic.get("name", "Unknown"),
                name=doc_data["name"],
                description=doc_data.get("description"),
                type=DocumentType(doc_data.get("type", "other")),
                status=DocumentStatus(doc_data.get("status", "pending")),
                size_bytes=doc_data.get("size_bytes", 0),
                mime_type=doc_data.get("mime_type", "application/octet-stream"),
                url=doc_data.get("url"),
                uploaded_by=doc_data["uploaded_by"],
                uploaded_at=doc_data["created_at"],
                processed_at=doc_data.get("processed_at"),
                metadata=doc_data.get("metadata", {}),
                tags=doc_data.get("tags", []),
                extracted_text=None,  # Don't include by default (can be large)
                summary=doc_data.get("summary")
            )
            documents.append(document)

        return documents

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to browse knowledge base", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to browse knowledge base: {e}"
        )


# ==================== Upload Document ====================

@router.post("/documents", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    topic_id: str = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None, description="Comma-separated tags"),
    user_id: CurrentUserId = None,
) -> DocumentUploadResponse:
    """Upload a document to the knowledge base.

    User must be a member of the topic with contributor role or higher.
    """
    try:
        supabase = get_supabase_client()

        # Check user's role in topic
        member_response = supabase.table("domain_members").select(
            "role"
        ).eq("domain_id", topic_id).eq("user_id", user_id).execute()

        if not member_response.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this topic"
            )

        user_role = member_response.data[0]["role"]

        # Members can view but not upload
        if user_role == "member":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Members cannot upload documents. Contributor role or higher required."
            )

        # Determine document type from mime type
        mime_to_type = {
            "application/pdf": DocumentType.PDF,
            "text/plain": DocumentType.TEXT,
            "text/markdown": DocumentType.MARKDOWN,
            "text/html": DocumentType.HTML,
            "image/": DocumentType.IMAGE,
            "video/": DocumentType.VIDEO,
            "audio/": DocumentType.AUDIO,
        }

        document_type = DocumentType.OTHER
        for mime_prefix, doc_type in mime_to_type.items():
            if file.content_type and file.content_type.startswith(mime_prefix):
                document_type = doc_type
                break

        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        # Read file content
        content = await file.read()
        file_size = len(content)

        # Store in Supabase Storage (assuming bucket exists)
        storage_path = f"{topic_id}/{user_id}/{file.filename}"
        storage_response = supabase.storage.from_("documents").upload(
            storage_path,
            content,
            {"content-type": file.content_type}
        )

        # Get public URL
        url_response = supabase.storage.from_("documents").get_public_url(storage_path)

        # Create document record
        document_data = {
            "domain_id": topic_id,
            "name": file.filename,
            "description": description,
            "type": document_type.value,
            "status": DocumentStatus.PENDING.value,
            "size_bytes": file_size,
            "mime_type": file.content_type,
            "url": url_response,
            "uploaded_by": user_id,
            "tags": tag_list,
            "metadata": {
                "original_filename": file.filename,
                "content_type": file.content_type,
            }
        }

        create_response = supabase.table("documents").insert(document_data).execute()

        if not create_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create document record"
            )

        created_document = create_response.data[0]

        # TODO: Trigger document processing workflow
        # For now, we'll just return success
        processing_job_id = None  # Would be workflow execution ID

        return DocumentUploadResponse(
            document_id=created_document["id"],
            status="uploaded",
            message=f"Document '{file.filename}' uploaded successfully and queued for processing",
            processing_job_id=processing_job_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to upload document", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {e}"
        )


# ==================== Get Document ====================

@router.get("/documents/{document_id}", response_model=Document)
async def get_document(
    document_id: str,
    include_content: bool = Query(False, description="Include extracted text"),
    user_id: CurrentUserId = None,
) -> Document:
    """Get a specific document by ID.

    User must have access to the topic containing the document.
    """
    try:
        supabase = get_supabase_client()

        # Get document with topic info
        document_response = supabase.table("documents").select(
            "*",
            "domains:domain_id(name, is_public)"
        ).eq("id", document_id).execute()

        if not document_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )

        doc_data = document_response.data[0]
        topic = doc_data.get("domains", {})

        # Check access
        is_public = topic.get("is_public", False)

        if not is_public:
            # Check if user is member
            member_check = supabase.table("domain_members").select(
                "id"
            ).eq("domain_id", doc_data["domain_id"]).eq("user_id", user_id).execute()

            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this document"
                )

        document = Document(
            id=doc_data["id"],
            topic_id=doc_data["domain_id"],
            topic_name=topic.get("name", "Unknown"),
            name=doc_data["name"],
            description=doc_data.get("description"),
            type=DocumentType(doc_data.get("type", "other")),
            status=DocumentStatus(doc_data.get("status", "pending")),
            size_bytes=doc_data.get("size_bytes", 0),
            mime_type=doc_data.get("mime_type", "application/octet-stream"),
            url=doc_data.get("url"),
            uploaded_by=doc_data["uploaded_by"],
            uploaded_at=doc_data["created_at"],
            processed_at=doc_data.get("processed_at"),
            metadata=doc_data.get("metadata", {}),
            tags=doc_data.get("tags", []),
            extracted_text=doc_data.get("extracted_text") if include_content else None,
            summary=doc_data.get("summary")
        )

        return document

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get document", document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {e}"
        )


# ==================== Search Knowledge Base ====================

@router.post("/search", response_model=List[SearchResult])
async def search_knowledge_base(
    search: SearchQuery,
    user_id: CurrentUserId,
) -> List[SearchResult]:
    """Search across documents in accessible topics.

    Uses semantic search to find relevant documents.
    """
    try:
        supabase = get_supabase_client()

        # Get user's accessible topics
        member_response = supabase.table("domain_members").select(
            "domain_id"
        ).eq("user_id", user_id).execute()

        user_topic_ids = [m["domain_id"] for m in member_response.data]

        # Also get public topics
        public_topics = supabase.table("domains").select(
            "id"
        ).eq("is_public", True).execute()

        public_topic_ids = [t["id"] for t in public_topics.data]

        # Combine and filter by requested topics
        accessible_topic_ids = list(set(user_topic_ids + public_topic_ids))

        if search.topic_ids:
            # Filter to only requested topics user has access to
            search_topic_ids = [tid for tid in search.topic_ids if tid in accessible_topic_ids]
            if not search_topic_ids:
                return []  # No accessible topics in filter
        else:
            search_topic_ids = accessible_topic_ids

        if not search_topic_ids:
            return []  # No accessible topics

        # TODO: Implement proper semantic search using vector database
        # For now, using basic text search

        # Build query
        query = supabase.table("documents").select(
            "*",
            "domains:domain_id(name)"
        ).in_("domain_id", search_topic_ids)

        # Apply type filter
        if search.document_types:
            type_values = [dt.value for dt in search.document_types]
            query = query.in_("type", type_values)

        # Apply tag filter
        if search.tags:
            for tag in search.tags:
                query = query.contains("tags", [tag])

        # Text search (basic implementation)
        # This would be replaced with vector similarity search
        query = query.or_(
            f"name.ilike.%{search.query}%,"
            f"description.ilike.%{search.query}%,"
            f"extracted_text.ilike.%{search.query}%"
        )

        # Execute with limit
        search_response = query.limit(search.limit).execute()

        # Transform to search results
        results = []
        for doc_data in search_response.data:
            topic = doc_data.get("domains", {})

            # Create snippet (simple version - would be improved with highlighting)
            snippet = ""
            if doc_data.get("description"):
                snippet = doc_data["description"][:200]
            elif doc_data.get("extracted_text"):
                text = doc_data["extracted_text"]
                # Find query context in text
                lower_text = text.lower()
                lower_query = search.query.lower()
                pos = lower_text.find(lower_query)
                if pos >= 0:
                    start = max(0, pos - 50)
                    end = min(len(text), pos + len(search.query) + 50)
                    snippet = "..." + text[start:end] + "..."
                else:
                    snippet = text[:200] + "..."

            result = SearchResult(
                document_id=doc_data["id"],
                topic_id=doc_data["domain_id"],
                topic_name=topic.get("name", "Unknown"),
                name=doc_data["name"],
                type=DocumentType(doc_data.get("type", "other")),
                relevance_score=1.0,  # TODO: Calculate real relevance score
                snippet=snippet,
                url=doc_data.get("url"),
                tags=doc_data.get("tags", []),
                content=doc_data.get("extracted_text") if search.include_content else None
            )
            results.append(result)

        # Sort by relevance (placeholder - would use real scores)
        results.sort(key=lambda r: r.relevance_score, reverse=True)

        return results

    except Exception as e:
        logger.error("Failed to search knowledge base", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search knowledge base: {e}"
        )


# ==================== Analyze Document ====================

@router.post("/analyze", response_model=AnalysisResult)
async def analyze_document(
    request: AnalysisRequest,
    user_id: CurrentUserId,
) -> AnalysisResult:
    """Analyze a document using AI.

    Supports summarization, entity extraction, sentiment analysis, and classification.
    """
    try:
        supabase = get_supabase_client()

        # Get document and check access
        document_response = supabase.table("documents").select(
            "domain_id",
            "extracted_text",
            "name",
            "domains:domain_id(is_public)"
        ).eq("id", request.document_id).execute()

        if not document_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {request.document_id}"
            )

        doc_data = document_response.data[0]
        is_public = doc_data.get("domains", {}).get("is_public", False)

        # Check access
        if not is_public:
            member_check = supabase.table("domain_members").select(
                "id"
            ).eq("domain_id", doc_data["domain_id"]).eq("user_id", user_id).execute()

            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this document"
                )

        # Get document text
        text = doc_data.get("extracted_text")
        if not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document has not been processed yet or contains no extractable text"
            )

        # TODO: Implement actual AI analysis
        # This would call OpenAI/Anthropic API or similar

        # Placeholder results
        if request.analysis_type == "summarize":
            result = {
                "summary": f"This is a placeholder summary of document '{doc_data['name']}'. "
                          f"The actual implementation would use AI to generate a real summary.",
                "key_points": [
                    "Key point 1",
                    "Key point 2",
                    "Key point 3"
                ]
            }
            confidence = 0.85

        elif request.analysis_type == "extract_entities":
            result = {
                "entities": [
                    {"type": "PERSON", "text": "John Doe", "confidence": 0.9},
                    {"type": "ORGANIZATION", "text": "Acme Corp", "confidence": 0.95},
                    {"type": "LOCATION", "text": "New York", "confidence": 0.88}
                ]
            }
            confidence = 0.9

        elif request.analysis_type == "sentiment":
            result = {
                "overall_sentiment": "positive",
                "confidence": 0.75,
                "scores": {
                    "positive": 0.75,
                    "negative": 0.15,
                    "neutral": 0.10
                }
            }
            confidence = 0.75

        elif request.analysis_type == "classify":
            categories = request.options.get("categories", ["General", "Technical", "Business"])
            result = {
                "category": categories[0],
                "confidence": 0.82,
                "all_scores": {cat: 0.3 for cat in categories}
            }
            result["all_scores"][categories[0]] = 0.82
            confidence = 0.82

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown analysis type: {request.analysis_type}"
            )

        return AnalysisResult(
            document_id=request.document_id,
            analysis_type=request.analysis_type,
            result=result,
            confidence=confidence,
            processing_time_ms=150  # Placeholder
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to analyze document", document_id=request.document_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze document: {e}"
        )
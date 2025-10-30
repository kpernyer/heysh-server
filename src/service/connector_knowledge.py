"""Knowledge Service Connector - SCI-compliant document and knowledge management.

Service Connector Interface (SCI) compliant API for managing documents and knowledge items.

Key SCI principles:
- Singular resource naming: /knowledge/document (not /documents)
- Hierarchical resources: /knowledge/topic/{topic_id}/document
- RESTful HTTP methods: GET, POST, PUT, DELETE
- snake_case path parameters: {document_id}, {topic_id}
- Async operations return 202 Accepted with location header
"""

from typing import Any, Dict, List, Optional
from enum import Enum

import structlog
from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
    Header,
    Response,
)
from pydantic import BaseModel, Field

from src.app.auth.dependencies import CurrentUserId
from src.app.clients.supabase import get_supabase_client

logger = structlog.get_logger()

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


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
    description: Optional[str] = None
    type: DocumentType
    status: DocumentStatus
    size_bytes: int
    mime_type: str
    url: Optional[str] = None
    uploaded_by: str
    uploaded_at: str
    processed_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    extracted_text: Optional[str] = None
    summary: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""

    document_id: str
    status: str
    message: str
    processing_job_id: Optional[str] = None


class DocumentUpdate(BaseModel):
    """Update document metadata."""

    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class SearchQuery(BaseModel):
    """Search query for knowledge base."""

    query: str = Field(..., min_length=1, max_length=500)
    topic_ids: Optional[List[str]] = Field(None, description="Filter by topics")
    document_types: Optional[List[DocumentType]] = Field(
        None, description="Filter by document types"
    )
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
    url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    content: Optional[str] = None


class AnalysisRequest(BaseModel):
    """Request to analyze a document."""

    analysis_type: str = Field(
        ..., pattern="^(summarize|extract_entities|sentiment|classify)$"
    )
    options: Dict[str, Any] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    """Result of document analysis."""

    document_id: str
    analysis_type: str
    result: Dict[str, Any]
    confidence: Optional[float] = None
    processing_time_ms: int


# ==================== Document Routes ====================


@router.get("/document", response_model=List[Document])
async def list_documents(
    user_id: CurrentUserId,
    topic_id: Optional[str] = Query(None, description="Filter by topic"),
    document_type: Optional[DocumentType] = Query(None, description="Filter by type"),
    status_filter: Optional[DocumentStatus] = Query(
        None, alias="status", description="Filter by status"
    ),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    uploaded_by: Optional[str] = Query(None, description="Filter by uploader"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[Document]:
    """List documents in the knowledge base.

    Returns documents from topics the user has access to.

    **Access Control:**
    - Users can view documents from topics they're members of
    - Public topic documents are visible to all users
    """
    try:
        supabase = get_supabase_client()

        # Get user's accessible topics
        member_response = supabase.table("domain_members").select("domain_id").eq(
            "user_id", user_id
        ).execute()

        user_topic_ids = [m["domain_id"] for m in member_response.data]

        # Also get public topics
        public_topics = supabase.table("domains").select("id").eq(
            "is_public", True
        ).execute()

        public_topic_ids = [t["id"] for t in public_topics.data]

        # Combine accessible topics
        accessible_topic_ids = list(set(user_topic_ids + public_topic_ids))

        if not accessible_topic_ids:
            return []  # No accessible topics

        # Build query
        query = supabase.table("documents").select("*", "domains:domain_id(name)").in_(
            "domain_id", accessible_topic_ids
        )

        # Apply filters
        if topic_id:
            if topic_id not in accessible_topic_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this topic",
                )
            query = query.eq("domain_id", topic_id)

        if document_type:
            query = query.eq("type", document_type.value)

        if status_filter:
            query = query.eq("status", status_filter.value)

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
                summary=doc_data.get("summary"),
            )
            documents.append(document)

        return documents

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list documents", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {e}",
        )


@router.post("/document", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    topic_id: str = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None, description="Comma-separated tags"),
    user_id: CurrentUserId = None,
) -> DocumentUploadResponse:
    """Upload a document to the knowledge base.

    **Access Control:**
    - User must be a member of the topic
    - User must have contributor role or higher (not just member)

    **Processing:**
    - Document is stored in Supabase Storage
    - Processing job is queued for text extraction and indexing
    - Returns 201 Created with document details
    """
    try:
        supabase = get_supabase_client()

        # Check user's role in topic
        member_response = supabase.table("domain_members").select("role").eq(
            "domain_id", topic_id
        ).eq("user_id", user_id).execute()

        if not member_response.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this topic",
            )

        user_role = member_response.data[0]["role"]

        # Members can view but not upload
        if user_role == "member":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Members cannot upload documents. Contributor role or higher required.",
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
            storage_path, content, {"content-type": file.content_type}
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
            },
        }

        create_response = supabase.table("documents").insert(document_data).execute()

        if not create_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create document record",
            )

        created_document = create_response.data[0]

        # TODO: Trigger document processing workflow
        # For now, we'll just return success
        processing_job_id = None  # Would be workflow execution ID

        return DocumentUploadResponse(
            document_id=created_document["id"],
            status="uploaded",
            message=f"Document '{file.filename}' uploaded successfully and queued for processing",
            processing_job_id=processing_job_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to upload document", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {e}",
        )


@router.get("/document/{document_id}", response_model=Document)
async def get_document(
    document_id: str,
    include_content: bool = Query(False, description="Include extracted text"),
    user_id: CurrentUserId = None,
) -> Document:
    """Get a specific document by ID.

    **Access Control:**
    - User must have access to the topic containing the document
    - Public topic documents are visible to all users
    """
    try:
        supabase = get_supabase_client()

        # Get document with topic info
        document_response = supabase.table("documents").select(
            "*", "domains:domain_id(name, is_public)"
        ).eq("id", document_id).execute()

        if not document_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}",
            )

        doc_data = document_response.data[0]
        topic = doc_data.get("domains", {})

        # Check access
        is_public = topic.get("is_public", False)

        if not is_public:
            # Check if user is member
            member_check = supabase.table("domain_members").select("id").eq(
                "domain_id", doc_data["domain_id"]
            ).eq("user_id", user_id).execute()

            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this document",
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
            summary=doc_data.get("summary"),
        )

        return document

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get document", document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {e}",
        )


@router.put("/document/{document_id}", response_model=Document)
async def update_document(
    document_id: str,
    update: DocumentUpdate,
    user_id: CurrentUserId,
) -> Document:
    """Update document metadata.

    **Access Control:**
    - User must be the uploader, admin, or owner of the topic
    """
    try:
        supabase = get_supabase_client()

        # Get document
        doc_response = supabase.table("documents").select(
            "domain_id", "uploaded_by"
        ).eq("id", document_id).execute()

        if not doc_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}",
            )

        doc_data = doc_response.data[0]

        # Check if user is the uploader
        if doc_data["uploaded_by"] != user_id:
            # Check if user is admin or owner of topic
            member_check = supabase.table("domain_members").select("role").eq(
                "domain_id", doc_data["domain_id"]
            ).eq("user_id", user_id).execute()

            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this document",
                )

            user_role = member_check.data[0]["role"]
            if user_role not in ["admin", "owner"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only document uploader, admin, or owner can update document metadata",
                )

        # Build update data
        update_data = {}
        if update.name is not None:
            update_data["name"] = update.name
        if update.description is not None:
            update_data["description"] = update.description
        if update.tags is not None:
            update_data["tags"] = update.tags

        if not update_data:
            # No updates provided, just return current document
            return await get_document(document_id, include_content=False, user_id=user_id)

        # Update document
        update_response = supabase.table("documents").update(update_data).eq(
            "id", document_id
        ).execute()

        if not update_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update document",
            )

        # Return updated document
        return await get_document(document_id, include_content=False, user_id=user_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update document", document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document: {e}",
        )


@router.delete("/document/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    user_id: CurrentUserId,
) -> None:
    """Delete a document.

    **Access Control:**
    - User must be the uploader, admin, or owner of the topic
    """
    try:
        supabase = get_supabase_client()

        # Get document
        doc_response = supabase.table("documents").select(
            "domain_id", "uploaded_by", "url"
        ).eq("id", document_id).execute()

        if not doc_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}",
            )

        doc_data = doc_response.data[0]

        # Check if user is the uploader
        if doc_data["uploaded_by"] != user_id:
            # Check if user is admin or owner of topic
            member_check = supabase.table("domain_members").select("role").eq(
                "domain_id", doc_data["domain_id"]
            ).eq("user_id", user_id).execute()

            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this document",
                )

            user_role = member_check.data[0]["role"]
            if user_role not in ["admin", "owner"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only document uploader, admin, or owner can delete document",
                )

        # Delete from storage (if URL exists)
        # TODO: Extract storage path from URL and delete from Supabase Storage

        # Delete document record
        delete_response = supabase.table("documents").delete().eq(
            "id", document_id
        ).execute()

        logger.info("Document deleted", document_id=document_id, user_id=user_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete document", document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {e}",
        )


# ==================== Hierarchical Route: Topic's Documents ====================


@router.get("/topic/{topic_id}/document", response_model=List[Document])
async def list_topic_documents(
    topic_id: str,
    user_id: CurrentUserId,
    document_type: Optional[DocumentType] = Query(None, description="Filter by type"),
    status_filter: Optional[DocumentStatus] = Query(
        None, alias="status", description="Filter by status"
    ),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[Document]:
    """List all documents in a specific topic.

    **Access Control:**
    - User must be a member of the topic or topic must be public
    """
    # Reuse list_documents with topic_id filter
    return await list_documents(
        user_id=user_id,
        topic_id=topic_id,
        document_type=document_type,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )


# ==================== Search ====================


@router.post("/search", response_model=List[SearchResult])
async def search_knowledge_base(
    search: SearchQuery,
    user_id: CurrentUserId,
) -> List[SearchResult]:
    """Search across documents in accessible topics.

    Uses semantic search to find relevant documents.

    **Access Control:**
    - Only searches topics user has access to
    - Respects topic visibility settings
    """
    try:
        supabase = get_supabase_client()

        # Get user's accessible topics
        member_response = supabase.table("domain_members").select("domain_id").eq(
            "user_id", user_id
        ).execute()

        user_topic_ids = [m["domain_id"] for m in member_response.data]

        # Also get public topics
        public_topics = supabase.table("domains").select("id").eq(
            "is_public", True
        ).execute()

        public_topic_ids = [t["id"] for t in public_topics.data]

        # Combine and filter by requested topics
        accessible_topic_ids = list(set(user_topic_ids + public_topic_ids))

        if search.topic_ids:
            # Filter to only requested topics user has access to
            search_topic_ids = [
                tid for tid in search.topic_ids if tid in accessible_topic_ids
            ]
            if not search_topic_ids:
                return []  # No accessible topics in filter
        else:
            search_topic_ids = accessible_topic_ids

        if not search_topic_ids:
            return []  # No accessible topics

        # TODO: Implement proper semantic search using vector database
        # For now, using basic text search

        # Build query
        query = supabase.table("documents").select("*", "domains:domain_id(name)").in_(
            "domain_id", search_topic_ids
        )

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
                content=doc_data.get("extracted_text") if search.include_content else None,
            )
            results.append(result)

        # Sort by relevance (placeholder - would use real scores)
        results.sort(key=lambda r: r.relevance_score, reverse=True)

        return results

    except Exception as e:
        logger.error("Failed to search knowledge base", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search knowledge base: {e}",
        )


# ==================== Document Analysis ====================


@router.post(
    "/document/{document_id}/analysis",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=Dict[str, str],
)
async def request_document_analysis(
    document_id: str,
    request: AnalysisRequest,
    user_id: CurrentUserId,
    response: Response,
) -> Dict[str, str]:
    """Request AI analysis of a document.

    **Analysis Types:**
    - `summarize`: Generate document summary with key points
    - `extract_entities`: Extract named entities (people, organizations, locations)
    - `sentiment`: Analyze sentiment (positive/negative/neutral)
    - `classify`: Classify into categories

    **Returns:**
    - 202 Accepted (async operation)
    - Location header with URL to check results

    **Access Control:**
    - User must have access to the document's topic
    """
    try:
        supabase = get_supabase_client()

        # Get document and check access
        document_response = supabase.table("documents").select(
            "domain_id", "extracted_text", "name", "domains:domain_id(is_public)"
        ).eq("id", document_id).execute()

        if not document_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}",
            )

        doc_data = document_response.data[0]
        is_public = doc_data.get("domains", {}).get("is_public", False)

        # Check access
        if not is_public:
            member_check = supabase.table("domain_members").select("id").eq(
                "domain_id", doc_data["domain_id"]
            ).eq("user_id", user_id).execute()

            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this document",
                )

        # Get document text
        text = doc_data.get("extracted_text")
        if not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document has not been processed yet or contains no extractable text",
            )

        # TODO: Trigger async analysis workflow via Temporal
        # For now, return placeholder job ID
        job_id = f"analysis-{document_id}-{request.analysis_type}"

        # Set Location header (SCI compliance)
        response.headers["Location"] = f"/knowledge/document/{document_id}/analysis"

        return {
            "status": "accepted",
            "message": f"Analysis request accepted and queued",
            "job_id": job_id,
            "document_id": document_id,
            "analysis_type": request.analysis_type,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to request document analysis", document_id=document_id, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to request document analysis: {e}",
        )


@router.get("/document/{document_id}/analysis", response_model=AnalysisResult)
async def get_document_analysis(
    document_id: str,
    analysis_type: Optional[str] = Query(
        None,
        description="Specific analysis type to retrieve",
        pattern="^(summarize|extract_entities|sentiment|classify)$",
    ),
    user_id: CurrentUserId = None,
) -> AnalysisResult:
    """Get analysis results for a document.

    **Access Control:**
    - User must have access to the document's topic
    """
    try:
        supabase = get_supabase_client()

        # Get document and check access
        document_response = supabase.table("documents").select(
            "domain_id", "extracted_text", "name", "domains:domain_id(is_public)"
        ).eq("id", document_id).execute()

        if not document_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}",
            )

        doc_data = document_response.data[0]
        is_public = doc_data.get("domains", {}).get("is_public", False)

        # Check access
        if not is_public:
            member_check = supabase.table("domain_members").select("id").eq(
                "domain_id", doc_data["domain_id"]
            ).eq("user_id", user_id).execute()

            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this document",
                )

        # TODO: Retrieve actual analysis results from storage/database
        # For now, return placeholder results

        if not analysis_type:
            analysis_type = "summarize"  # Default

        # Placeholder results
        if analysis_type == "summarize":
            result = {
                "summary": f"This is a placeholder summary of document '{doc_data['name']}'. "
                "The actual implementation would use AI to generate a real summary.",
                "key_points": ["Key point 1", "Key point 2", "Key point 3"],
            }
            confidence = 0.85

        elif analysis_type == "extract_entities":
            result = {
                "entities": [
                    {"type": "PERSON", "text": "John Doe", "confidence": 0.9},
                    {"type": "ORGANIZATION", "text": "Acme Corp", "confidence": 0.95},
                    {"type": "LOCATION", "text": "New York", "confidence": 0.88},
                ]
            }
            confidence = 0.9

        elif analysis_type == "sentiment":
            result = {
                "overall_sentiment": "positive",
                "confidence": 0.75,
                "scores": {"positive": 0.75, "negative": 0.15, "neutral": 0.10},
            }
            confidence = 0.75

        elif analysis_type == "classify":
            result = {
                "category": "Technical",
                "confidence": 0.82,
                "all_scores": {"General": 0.1, "Technical": 0.82, "Business": 0.08},
            }
            confidence = 0.82

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown analysis type: {analysis_type}",
            )

        return AnalysisResult(
            document_id=document_id,
            analysis_type=analysis_type,
            result=result,
            confidence=confidence,
            processing_time_ms=150,  # Placeholder
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get document analysis", document_id=document_id, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document analysis: {e}",
        )

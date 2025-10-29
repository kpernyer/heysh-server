"""Data management routes (domains, workflows, documents)."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status

from src.service.models import (
    WorkflowModel,
)
from src.app.auth.dependencies import CurrentUserId
from src.app.clients.supabase import get_supabase_client
from src.app.schemas.requests import (
    WorkflowDataRequest,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1", tags=["data"])


# ==================== Workflow Management ====================


@router.get("/workflows")
async def list_workflows(
    topic_id: str | None = None,
    user_id: CurrentUserId = None,
) -> dict[str, Any]:
    """List workflows, optionally filtered by topic.

    Requires: Valid JWT token in Authorization header

    Query params:
        - topic_id: Filter by topic UUID (optional)
    """
    try:
        if topic_id:
            workflows = await WorkflowModel.get_by_domain(topic_id)
        else:
            workflows = await WorkflowModel.list_all()

        return {
            "workflows": workflows,
            "count": len(workflows),
        }

    except Exception as e:
        logger.error("Failed to list workflows", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflows: {e!s}",
        )


@router.get("/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: str, user_id: CurrentUserId = None
) -> dict[str, Any]:
    """Get a specific workflow by ID. Requires: Valid JWT token."""
    try:
        workflow = await WorkflowModel.get_by_id(workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {workflow_id}",
            )
        return workflow

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get workflow", workflow_id=workflow_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow: {e!s}",
        )


@router.post("/workflows", status_code=status.HTTP_201_CREATED)
async def create_workflow(
    request: WorkflowDataRequest,
    user_id: CurrentUserId = None,
) -> dict[str, Any]:
    """Create a new workflow.

    Requires: Valid JWT token in Authorization header

    Request body:
        - name: Workflow name
        - topic_id: Topic UUID
        - yaml_definition: Workflow definition as dict
        - description: Optional description
    """
    try:
        workflow = await WorkflowModel.create_workflow(
            name=request.name,
            domain_id=request.topic_id,
            yaml_definition=request.yaml_definition,
            description=request.description,
        )

        logger.info("Workflow created", workflow_id=workflow["id"])

        return workflow

    except Exception as e:
        logger.error("Failed to create workflow", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow: {e!s}",
        )


@router.put("/workflows/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    request: WorkflowDataRequest,
    user_id: CurrentUserId = None,
) -> dict[str, Any]:
    """Update an existing workflow. Requires: Valid JWT token."""
    try:
        workflow_data = {
            "name": request.name,
            "description": request.description,
            "yaml_definition": request.yaml_definition,
            "is_active": request.is_active,
        }

        workflow = await WorkflowModel.update(workflow_id, workflow_data)

        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {workflow_id}",
            )

        logger.info("Workflow updated", workflow_id=workflow_id)

        return workflow

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update workflow", workflow_id=workflow_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update workflow: {e!s}",
        )


@router.delete("/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(workflow_id: str, user_id: CurrentUserId = None) -> None:
    """Delete a workflow. Requires: Valid JWT token."""
    try:
        success = await WorkflowModel.delete(workflow_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {workflow_id}",
            )

        logger.info("Workflow deleted", workflow_id=workflow_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete workflow", workflow_id=workflow_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete workflow: {e!s}",
        )


# ==================== Document Management ====================


@router.get("/documents")
async def list_documents(
    topic_id: str | None = None,
    user_id: CurrentUserId = None,
) -> dict[str, Any]:
    """List documents, optionally filtered by topic.

    Requires: Valid JWT token in Authorization header

    Query params:
        - topic_id: Filter by topic UUID (optional)
    """
    try:
        supabase = get_supabase_client()

        query = supabase.table("documents").select("*")

        if topic_id:
            query = query.eq("topic_id", topic_id)

        response = query.execute()

        return {
            "documents": response.data,
            "count": len(response.data),
        }

    except Exception as e:
        logger.error("Failed to list documents", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {e!s}",
        )


@router.get("/documents/{document_id}")
async def get_document(
    document_id: str, user_id: CurrentUserId = None
) -> dict[str, Any]:
    """Get a specific document by ID. Requires: Valid JWT token."""
    try:
        supabase = get_supabase_client()

        response = (
            supabase.table("documents")
            .select("*")
            .eq("id", document_id)
            .single()
            .execute()
        )

        return response.data

    except Exception as e:
        logger.error("Failed to get document", document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str, user_id: CurrentUserId = None) -> None:
    """Delete a document. Requires: Valid JWT token."""
    try:
        supabase = get_supabase_client()

        response = supabase.table("documents").delete().eq("id", document_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}",
            )

        logger.info("Document deleted", document_id=document_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete document", document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {e!s}",
        )


# ==================== Topic Management ====================


@router.get("/topics")
async def list_topics(user_id: CurrentUserId = None) -> dict[str, Any]:
    """List all topics. Requires: Valid JWT token."""
    try:
        supabase = get_supabase_client()

        response = supabase.table("topics").select("*").execute()

        return {
            "topics": response.data,
            "count": len(response.data),
        }

    except Exception as e:
        logger.error("Failed to list topics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list topics: {e!s}",
        )


@router.get("/topics/search")
async def search_topics(
    q: str,
    user_id: CurrentUserId = None,
    use_llm: bool = True,
) -> dict[str, Any]:
    """Semantic search across topics using Weaviate + Neo4j + LLM.

    Query params:
        - q: Search query (required)
        - use_llm: Whether to use LLM to summarize results (default: true)
    """
    logger.info("Searching topics", query=q[:50], use_llm=use_llm)

    from activity.domain import search_domains_activity
    from src.app.clients.llm import get_llm_client

    try:
        # 1. Search in Weaviate and Neo4j
        search_results = await search_domains_activity(
            {
                "query": q,
                "user_id": user_id,
            }
        )

        # 2. Optionally use LLM to summarize and present results
        if use_llm and (
            search_results["vector_results"] or search_results["graph_results"]
        ):
            llm = get_llm_client()

            # Prepare context for LLM
            vector_topics = search_results["vector_results"]
            graph_topics = search_results["graph_results"]

            context = "Vector search results (semantic similarity):\n"
            for idx, topic in enumerate(vector_topics[:5], 1):
                context += f"{idx}. {topic['name']}: {topic.get('description', 'No description')}\n"

            context += "\nGraph search results (keyword + relationships):\n"
            for idx, topic in enumerate(graph_topics[:5], 1):
                is_member = " (you are a member)" if topic.get("is_member") else ""
                context += f"{idx}. {topic['name']}: {topic.get('description', 'No description')}{is_member}\n"

            # Generate LLM summary
            prompt = f"""Based on the user's search query: "{q}"

Here are the relevant topics found:

{context}

Please provide a helpful summary of these topics, highlighting the most relevant ones for the user's query. Be concise and actionable."""

            llm_response = await llm.generate(
                prompt=prompt,
                system="You are a helpful assistant that summarizes search results for a knowledge management platform.",
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=500,
            )

            summary = llm_response["answer"]
        else:
            summary = None

        return {
            "query": q,
            "results": {
                "vector_results": search_results["vector_results"],
                "graph_results": search_results["graph_results"],
            },
            "summary": summary,
            "result_count": {
                "vector": len(search_results["vector_results"]),
                "graph": len(search_results["graph_results"]),
            },
        }

    except Exception as e:
        logger.error("Search failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {e!s}",
        )


@router.get("/topics/{topic_id}")
async def get_topic(topic_id: str, user_id: CurrentUserId = None) -> dict[str, Any]:
    """Get a specific topic by ID. Requires: Valid JWT token."""
    try:
        supabase = get_supabase_client()

        response = (
            supabase.table("topics").select("*").eq("id", topic_id).single().execute()
        )

        return response.data

    except Exception as e:
        logger.error("Failed to get topic", topic_id=topic_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic not found: {topic_id}",
        )


# ==================== Workflow Results/Status ====================


@router.get("/workflows/{workflow_id}/results")
async def get_workflow_results(
    workflow_id: str,
    user_id: CurrentUserId = None,
) -> dict[str, Any]:
    """Get workflow results/outputs.

    Requires: Valid JWT token in Authorization header

    This endpoint returns the final output of a completed workflow
    from Temporal (via the backend).
    """
    try:
        supabase = get_supabase_client()

        # Check if workflow exists and get its status
        workflow = (
            supabase.table("workflows")
            .select("*")
            .eq("id", workflow_id)
            .single()
            .execute()
        )

        if not workflow.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {workflow_id}",
            )

        # Try to get execution results from a results table (if you have one)
        try:
            results = (
                supabase.table("workflow_executions")
                .select("*")
                .eq("workflow_id", workflow_id)
                .order("created_at", desc=True)
                .limit(1)
                .single()
                .execute()
            )

            return {
                "workflow_id": workflow_id,
                "results": results.data,
            }
        except Exception:
            # No results yet
            return {
                "workflow_id": workflow_id,
                "results": None,
                "message": "Workflow is still processing or no results available",
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get workflow results", workflow_id=workflow_id, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow results: {e!s}",
        )

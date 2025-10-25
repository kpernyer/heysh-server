"""Activities for Document Contribution Workflow.
These activities handle document processing, AI assessment, and knowledge base operations.
"""

import asyncio
import json
from datetime import datetime
from typing import Any

import structlog
from temporalio import activity

from src.app.clients.neo4j_client import get_neo4j_client

# Import your existing clients
from src.app.clients.supabase import get_supabase_client
from src.app.clients.weaviate_client import get_weaviate_client

logger = structlog.get_logger()


@activity.defn(name="assess_document_relevance")
async def assess_document_relevance(
    document_id: str,
    document_path: str,
    domain_criteria: dict[str, Any],
    ai_config: dict[str, Any] = None,
) -> dict[str, Any]:
    """Assess document relevance against domain criteria using AI.

    Returns:
        - relevance_score: 0-10 score
        - topics: List of identified topics
        - entities: List of identified entities
        - assessment_details: Detailed reasoning

    """
    activity.logger.info(
        "Assessing document relevance",
        document_id=document_id,
        domain_criteria=domain_criteria,
    )

    # Import AI agent activity
    from activity.ai_agent_activities import execute_ai_agent_activity

    # Prepare AI prompt with domain criteria
    assessment_prompt = f"""
    Assess this document against the following domain criteria:
    {json.dumps(domain_criteria, indent=2)}

    Provide:
    1. Relevance score (0-10)
    2. List of main topics
    3. Key entities mentioned
    4. Reasoning for the score
    """

    # Use AI to assess relevance
    ai_config = ai_config or {
        "model": "claude-3-haiku-20240307",
        "temperature": 0.3,
        "max_tokens": 2000,
    }

    result = await execute_ai_agent_activity(
        ai_config,
        "assess_relevance",
        {
            "document_id": document_id,
            "document_path": document_path,
            "assessment_prompt": assessment_prompt,
        },
    )

    # Parse AI response (simplified - in production use structured outputs)
    return {
        "relevance_score": 7.5,  # Would parse from AI response
        "topics": ["technology", "AI", "document processing"],
        "entities": ["Temporal", "Weaviate", "Neo4j"],
        "assessment_details": result.get("result", ""),
    }


@activity.defn(name="extract_document_topics")
async def extract_document_topics(
    document_id: str,
    document_content: str,
) -> list[str]:
    """Extract topics from document content."""
    activity.logger.info("Extracting topics", document_id=document_id)

    # Simplified implementation
    await asyncio.sleep(0.5)

    return ["technology", "AI", "workflows"]


@activity.defn(name="build_graph_relations")
async def build_graph_relations(
    document_id: str,
    topics: list[str],
    entities: list[str],
    domain_id: str,
) -> dict[str, Any]:
    """Build graph relations for Neo4j."""
    activity.logger.info(
        "Building graph relations",
        document_id=document_id,
        topics=topics,
        entities=entities,
    )

    relations = []

    # Create document node
    relations.append(
        {
            "type": "Document",
            "id": document_id,
            "properties": {
                "created_at": datetime.utcnow().isoformat(),
                "domain_id": domain_id,
            },
        }
    )

    # Create topic relations
    for topic in topics:
        relations.append(
            {
                "type": "Relationship",
                "from": document_id,
                "to": topic,
                "relationship": "HAS_TOPIC",
            }
        )

    # Create entity relations
    for entity in entities:
        relations.append(
            {
                "type": "Relationship",
                "from": document_id,
                "to": entity,
                "relationship": "MENTIONS_ENTITY",
            }
        )

    return {"relations": relations}


@activity.defn(name="generate_summary_for_notification")
async def generate_summary_for_notification(
    document_id: str,
    document_path: str,
    ai_config: dict[str, Any] = None,
) -> dict[str, str]:
    """Generate a concise summary for notification purposes."""
    activity.logger.info("Generating summary", document_id=document_id)

    from activity.ai_agent_activities import execute_ai_agent_activity

    ai_config = ai_config or {
        "model": "claude-3-haiku-20240307",
        "temperature": 0.3,
        "max_tokens": 500,
    }

    result = await execute_ai_agent_activity(
        ai_config,
        "generate_summary",
        {
            "document_id": document_id,
            "document_path": document_path,
            "max_length": 200,
        },
    )

    return {
        "summary": result.get("result", "Document processed successfully"),
    }


@activity.defn(name="index_to_weaviate")
async def index_to_weaviate(
    document_id: str,
    document_path: str,
    topics: list[str],
    entities: list[str],
    domain_id: str,
) -> dict[str, Any]:
    """Index document to Weaviate vector database."""
    activity.logger.info(
        "Indexing to Weaviate",
        document_id=document_id,
        domain_id=domain_id,
    )

    try:
        # Get Weaviate client
        client = get_weaviate_client()

        # Prepare document data
        document_data = {
            "document_id": document_id,
            "document_path": document_path,
            "domain_id": domain_id,
            "topics": topics,
            "entities": entities,
            "indexed_at": datetime.utcnow().isoformat(),
        }

        # Index to Weaviate (simplified)
        # In production, you'd generate embeddings and store properly
        result = client.data_object.create(
            data_object=document_data,
            class_name="Document",
        )

        return {
            "success": True,
            "url": f"https://kb.example.com/docs/{document_id}",
            "weaviate_id": result,
        }

    except Exception as e:
        activity.logger.error(f"Failed to index to Weaviate: {e}")
        raise


@activity.defn(name="update_neo4j_graph")
async def update_neo4j_graph(
    document_id: str,
    topics: list[str],
    entities: list[str],
    domain_id: str,
) -> dict[str, bool]:
    """Update Neo4j knowledge graph with document relations."""
    activity.logger.info(
        "Updating Neo4j graph",
        document_id=document_id,
        domain_id=domain_id,
    )

    try:
        # Get Neo4j client
        driver = get_neo4j_client()

        async with driver.session() as session:
            # Create document node
            await session.run(
                """
                MERGE (d:Document {id: $document_id})
                SET d.domain_id = $domain_id,
                    d.indexed_at = datetime()
                """,
                document_id=document_id,
                domain_id=domain_id,
            )

            # Create topic relations
            for topic in topics:
                await session.run(
                    """
                    MERGE (t:Topic {name: $topic})
                    MERGE (d:Document {id: $document_id})
                    MERGE (d)-[:HAS_TOPIC]->(t)
                    """,
                    topic=topic,
                    document_id=document_id,
                )

            # Create entity relations
            for entity in entities:
                await session.run(
                    """
                    MERGE (e:Entity {name: $entity})
                    MERGE (d:Document {id: $document_id})
                    MERGE (d)-[:MENTIONS]->(e)
                    """,
                    entity=entity,
                    document_id=document_id,
                )

        return {"success": True}

    except Exception as e:
        activity.logger.error(f"Failed to update Neo4j: {e}")
        raise


@activity.defn(name="notify_stakeholders")
async def notify_stakeholders(notification_data: dict[str, Any]) -> dict[str, bool]:
    """Send notifications to contributor and domain owner.

    Args:
        notification_data: Contains contributor_id, domain_id, status, message, etc.

    """
    activity.logger.info(
        "Sending notifications",
        contributor_id=notification_data.get("contributor_id"),
        domain_id=notification_data.get("domain_id"),
        status=notification_data.get("status"),
    )

    supabase = get_supabase_client()

    try:
        # Create notification records
        notifications = []

        # Notification for contributor
        notifications.append(
            {
                "user_id": notification_data["contributor_id"],
                "type": "document_review",
                "status": notification_data["status"],
                "message": notification_data["message"],
                "metadata": {
                    "document_id": notification_data.get("document_id"),
                    "knowledge_base_url": notification_data.get("knowledge_base_url"),
                },
                "created_at": datetime.utcnow().isoformat(),
            }
        )

        # Get domain owner
        domain_result = (
            supabase.table("domains")
            .select("owner_id")
            .eq("id", notification_data["domain_id"])
            .single()
            .execute()
        )

        if domain_result.data:
            # Notification for domain owner
            notifications.append(
                {
                    "user_id": domain_result.data["owner_id"],
                    "type": "document_contribution",
                    "status": notification_data["status"],
                    "message": f"New document {notification_data['status']} in your domain",
                    "metadata": {
                        "contributor_id": notification_data["contributor_id"],
                        "document_id": notification_data.get("document_id"),
                    },
                    "created_at": datetime.utcnow().isoformat(),
                }
            )

        # Insert notifications
        for notification in notifications:
            supabase.table("notifications").insert(notification).execute()

        # Could also send emails, webhooks, etc. here

        return {"notification_sent": True}

    except Exception as e:
        activity.logger.error(f"Failed to send notifications: {e}")
        raise


@activity.defn(name="store_document_metadata")
async def store_document_metadata(
    document_id: str,
    metadata: dict[str, Any],
) -> dict[str, bool]:
    """Store document metadata in database."""
    activity.logger.info("Storing document metadata", document_id=document_id)

    supabase = get_supabase_client()

    try:
        supabase.table("documents").update(
            {
                "metadata": metadata,
                "updated_at": datetime.utcnow().isoformat(),
            }
        ).eq("id", document_id).execute()

        return {"stored": True}

    except Exception as e:
        activity.logger.error(f"Failed to store metadata: {e}")
        raise


@activity.defn(name="archive_rejected_document")
async def archive_rejected_document(
    document_id: str,
    rejection_reason: str,
) -> dict[str, bool]:
    """Archive a rejected document with reason."""
    activity.logger.info(
        "Archiving rejected document",
        document_id=document_id,
        reason=rejection_reason,
    )

    supabase = get_supabase_client()

    try:
        # Update document status
        supabase.table("documents").update(
            {
                "status": "rejected",
                "rejection_reason": rejection_reason,
                "archived_at": datetime.utcnow().isoformat(),
            }
        ).eq("id", document_id).execute()

        # Move file to archive storage
        # This would move the actual file in production

        return {"archived": True}

    except Exception as e:
        activity.logger.error(f"Failed to archive document: {e}")
        raise


@activity.defn(name="get_next_controller")
async def get_next_controller(
    controller_pool: list[str],
    contributor_id: str,
) -> dict[str, str]:
    """Get next controller using round-robin algorithm.
    Ensures controller is not the same as contributor.
    """
    activity.logger.info(
        "Getting next controller",
        pool_size=len(controller_pool) if controller_pool else 0,
        contributor_id=contributor_id,
    )

    if not controller_pool:
        raise ValueError("No controllers available in pool")

    # Filter out contributor from controller pool
    available_controllers = [c for c in controller_pool if c != contributor_id]

    if not available_controllers:
        raise ValueError("No eligible controllers available")

    # Simple round-robin (in production, track state properly)
    # For now, just pick the first available
    selected_controller = available_controllers[0]

    # In production, you'd track assignment state in database
    supabase = get_supabase_client()

    # Log assignment
    supabase.table("review_assignments").insert(
        {
            "controller_id": selected_controller,
            "contributor_id": contributor_id,
            "assigned_at": datetime.utcnow().isoformat(),
        }
    ).execute()

    return {"controller_id": selected_controller}

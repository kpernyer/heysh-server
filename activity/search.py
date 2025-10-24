"""Search and indexing activities."""

from typing import Any

import structlog
from temporalio import activity

from src.app.clients.neo4j import get_neo4j_client
from src.app.clients.weaviate import get_weaviate_client

logger = structlog.get_logger()


@activity.defn
async def search_documents_activity(
    query: str, domain_id: str, limit: int = 10
) -> list[dict[str, Any]]:
    """Search for relevant documents using vector search.

    Args:
        query: Search query
        domain_id: Domain to search within
        limit: Maximum number of results

    Returns:
        List of matching documents with scores

    """
    activity.logger.info("Searching documents", query=query, domain_id=domain_id)

    weaviate = get_weaviate_client()
    results = await weaviate.search(
        collection="Documents",
        query=query,
        filters={"domain_id": domain_id},
        limit=limit,
    )

    activity.logger.info("Search completed", result_count=len(results))
    return results


@activity.defn
async def find_related_documents_activity(doc_ids: list[str]) -> list[dict[str, Any]]:
    """Find related documents using graph traversal.

    Args:
        doc_ids: List of document IDs to find relations for

    Returns:
        List of related documents

    """
    activity.logger.info("Finding related documents", doc_count=len(doc_ids))

    neo4j = get_neo4j_client()

    query = """
    MATCH (d:Document)-[:RELATED_TO|REFERENCES*1..2]->(rd:Document)
    WHERE d.id IN $doc_ids
    RETURN DISTINCT rd.id AS document_id,
                    rd.title AS title,
                    rd.quality_score AS quality_score,
                    rd.domain_id AS domain_id
    ORDER BY rd.quality_score DESC
    LIMIT 5
    """

    results = await neo4j.run_query(query, {"doc_ids": doc_ids})

    activity.logger.info("Related documents found", count=len(results))
    return results


@activity.defn
async def index_weaviate_activity(data: dict[str, Any]) -> dict[str, Any]:
    """Index document in Weaviate for vector search.

    Args:
        data: Document data including embeddings

    Returns:
        Indexing result

    """
    activity.logger.info("Indexing in Weaviate", document_id=data["document_id"])

    weaviate = get_weaviate_client()

    # Create document object in Weaviate
    result = await weaviate.index_document(
        collection="Documents",
        document_id=data["document_id"],
        domain_id=data["domain_id"],
        text=data["text"],
        chunks=data.get("chunks", []),
        embeddings=data["embeddings"],
        metadata=data.get("metadata", {}),
    )

    activity.logger.info("Weaviate indexing completed", success=result["success"])
    return result


@activity.defn
async def update_neo4j_graph_activity(data: dict[str, Any]) -> dict[str, Any]:
    """Update Neo4j knowledge graph with document relationships.

    Args:
        data: Document data including entities and topics

    Returns:
        Update result

    """
    activity.logger.info("Updating Neo4j graph", document_id=data["document_id"])

    neo4j = get_neo4j_client()

    # Create document node
    create_doc_query = """
    MERGE (d:Document {id: $document_id})
    SET d.domain_id = $domain_id,
        d.updated_at = datetime()
    """

    await neo4j.run_query(
        create_doc_query,
        {
            "document_id": data["document_id"],
            "domain_id": data["domain_id"],
        },
    )

    # Create topic nodes and relationships
    for topic in data.get("topics", []):
        topic_query = """
        MERGE (t:Topic {name: $topic_name})
        WITH t
        MATCH (d:Document {id: $document_id})
        MERGE (d)-[:HAS_TOPIC]->(t)
        """
        await neo4j.run_query(
            topic_query,
            {
                "topic_name": topic,
                "document_id": data["document_id"],
            },
        )

    # Create entity nodes and relationships
    for entity in data.get("entities", []):
        entity_query = """
        MERGE (e:Entity {name: $entity_name, type: $entity_type})
        WITH e
        MATCH (d:Document {id: $document_id})
        MERGE (d)-[:MENTIONS]->(e)
        """
        await neo4j.run_query(
            entity_query,
            {
                "entity_name": entity.get("name"),
                "entity_type": entity.get("type", "UNKNOWN"),
                "document_id": data["document_id"],
            },
        )

    activity.logger.info("Neo4j graph updated successfully")
    return {"success": True, "document_id": data["document_id"]}

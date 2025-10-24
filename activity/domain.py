"""Domain management activities."""

from typing import Any

import structlog
from temporalio import activity

from src.app.clients.neo4j import get_neo4j_client
from src.app.clients.weaviate import get_weaviate_client
from src.app.utils.embeddings import generate_embedding

logger = structlog.get_logger()


@activity.defn
async def index_domain_activity(domain_data: dict[str, Any]) -> dict[str, str]:
    """Index domain in Weaviate and Neo4j for semantic search.

    Args:
        domain_data: Contains domain_id, name, description, created_by, etc.

    Returns:
        Dictionary with indexing results

    """
    activity.logger.info("Indexing domain", domain_id=domain_data["domain_id"])

    domain_id = domain_data["domain_id"]
    name = domain_data["name"]
    description = domain_data.get("description", "")
    created_by = domain_data["created_by"]

    # Create searchable text from domain info
    searchable_text = f"{name}\n{description}"

    # 1. Generate embedding
    embedding = await generate_embedding(searchable_text)

    # 2. Index in Weaviate for vector search
    weaviate_client = get_weaviate_client()

    # Create or update domain object in Weaviate
    domain_object = {
        "domain_id": domain_id,
        "name": name,
        "description": description,
        "created_by": created_by,
        "text": searchable_text,
        "type": "domain",
    }

    # Store with vector using Weaviate v4 API
    collection = weaviate_client.client.collections.get("Domain")
    weaviate_result = collection.data.insert(
        properties=domain_object,
        vector=embedding,
    )

    # 3. Index in Neo4j for graph relationships
    neo4j = get_neo4j_client()

    neo4j_result = await neo4j.run_query(
        """
        MERGE (d:Domain {id: $domain_id})
        SET d.name = $name,
            d.description = $description,
            d.created_at = datetime(),
            d.created_by = $created_by
        WITH d
        MERGE (u:User {id: $created_by})
        MERGE (u)-[:CREATED]->(d)
        RETURN d.id as domain_id
        """,
        {
            "domain_id": domain_id,
            "name": name,
            "description": description,
            "created_by": created_by,
        },
    )

    activity.logger.info(
        "Domain indexed successfully",
        domain_id=domain_id,
        weaviate_id=weaviate_result,
    )

    return {
        "domain_id": domain_id,
        "weaviate_id": str(weaviate_result),
        "neo4j_indexed": True,
    }


@activity.defn
async def search_domains_activity(search_data: dict[str, Any]) -> dict[str, Any]:
    """Search domains using semantic search in Weaviate and graph traversal in Neo4j.

    Args:
        search_data: Contains query string and optional user_id for personalization

    Returns:
        Combined search results from Weaviate and Neo4j

    """
    query = search_data["query"]
    user_id = search_data.get("user_id")

    activity.logger.info("Searching domains", query=query[:50])

    # 1. Vector search in Weaviate
    query_embedding = await generate_embedding(query)
    weaviate_client = get_weaviate_client()

    # Use Weaviate v4 API
    collection = weaviate_client.client.collections.get("Domain")
    response = collection.query.near_vector(
        near_vector=query_embedding,
        limit=10,
        return_metadata=["distance", "certainty"],
    )

    # Format results
    weaviate_results = {
        "data": {
            "Get": {
                "Domain": [
                    {
                        "domain_id": obj.properties.get("domain_id"),
                        "name": obj.properties.get("name"),
                        "description": obj.properties.get("description"),
                        "created_by": obj.properties.get("created_by"),
                    }
                    for obj in response.objects
                ]
            }
        }
    }

    # 2. Graph search in Neo4j (find related domains)
    neo4j = get_neo4j_client()

    # Find domains user has access to or created
    neo4j_results = await neo4j.run_query(
        """
        MATCH (d:Domain)
        WHERE d.name CONTAINS $query_fragment
           OR d.description CONTAINS $query_fragment
        OPTIONAL MATCH (d)<-[:MEMBER_OF]-(u:User {id: $user_id})
        OPTIONAL MATCH (d)<-[:CREATED]-(creator:User)
        RETURN d.id as domain_id,
               d.name as name,
               d.description as description,
               d.created_by as created_by,
               creator.name as creator_name,
               COUNT(u) > 0 as is_member
        LIMIT 10
        """,
        {
            "query_fragment": query,
            "user_id": user_id or "",
        },
    )

    # 3. Combine results
    combined_results = {
        "vector_results": weaviate_results.get("data", {})
        .get("Get", {})
        .get("Domain", []),
        "graph_results": neo4j_results,
        "query": query,
    }

    activity.logger.info(
        "Search completed",
        vector_count=len(combined_results["vector_results"]),
        graph_count=len(combined_results["graph_results"]),
    )

    return combined_results

"""Neo4j client."""

import os
from functools import lru_cache
from typing import Any

from neo4j import AsyncDriver, AsyncGraphDatabase


class Neo4jClient:
    """Neo4j graph database client."""

    def __init__(self, uri: str, user: str, password: str) -> None:
        """Initialize Neo4j client."""
        self.driver: AsyncDriver = AsyncGraphDatabase.driver(
            uri,
            auth=(user, password),
        )

    async def close(self) -> None:
        """Close driver connection."""
        await self.driver.close()

    async def run_query(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Run Cypher query.

        Args:
            query: Cypher query string
            params: Query parameters

        Returns:
            List of result records

        """
        async with self.driver.session() as session:
            result = await session.run(query, params or {})
            records = [record.data() async for record in result]
            return records

    async def create_document_node(
        self,
        document_id: str,
        domain_id: str,
        metadata: dict[str, Any],
    ) -> None:
        """Create or update document node."""
        query = """
        MERGE (d:Document {id: $document_id})
        SET d.domain_id = $domain_id,
            d.updated_at = datetime(),
            d += $metadata
        """
        await self.run_query(
            query,
            {
                "document_id": document_id,
                "domain_id": domain_id,
                "metadata": metadata,
            },
        )

    async def create_relationship(
        self,
        from_id: str,
        to_id: str,
        relationship_type: str,
    ) -> None:
        """Create relationship between nodes."""
        query = f"""
        MATCH (a:Document {{id: $from_id}})
        MATCH (b:Document {{id: $to_id}})
        MERGE (a)-[r:{relationship_type}]->(b)
        SET r.created_at = datetime()
        """
        await self.run_query(
            query,
            {"from_id": from_id, "to_id": to_id},
        )


@lru_cache(maxsize=1)
def get_neo4j_client() -> Neo4jClient:
    """Get Neo4j client (singleton).

    Returns:
        Neo4jClient instance

    """
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    return Neo4jClient(uri, user, password)

"""GraphQL resolvers for complex queries"""

import json
from datetime import datetime

import structlog
import weaviate
from neo4j import AsyncGraphDatabase
from supabase import create_client
from temporalio.client import Client as TemporalClient
from temporalio.contrib.pydantic import pydantic_data_converter

from ..config import get_settings

logger = structlog.get_logger()
from .types import (
    Domain,
    DomainStats,
    KnowledgeGraph,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
    SearchResponse,
    SearchResult,
    WorkflowInfo,
    WorkflowStatus,
)

settings = get_settings()


class GraphQLResolvers:
    """Resolvers for GraphQL queries and mutations"""

    def __init__(self):
        # Initialize database connections
        self.neo4j_driver = None
        self.weaviate_client = None
        self.temporal_client = None
        self.supabase_client = None

    async def init_connections(self):
        """Initialize async database connections"""
        try:
            # Neo4j
            if settings.neo4j_uri:
                self.neo4j_driver = AsyncGraphDatabase.driver(
                    settings.neo4j_uri,
                    auth=(settings.neo4j_user, settings.neo4j_password),
                )
                logger.info("Neo4j connected", uri=settings.neo4j_uri)

            # Weaviate - using v4 client syntax
            if settings.weaviate_url:
                self.weaviate_client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=settings.weaviate_url.replace("https://", "").replace(
                        "http://", ""
                    ),
                    auth_credentials=weaviate.auth.AuthApiKey(
                        api_key=settings.weaviate_api_key
                    ),
                )
                logger.info("Weaviate connected", url=settings.weaviate_url)

            # Temporal
            if settings.temporal_address:
                from temporalio.client import TLSConfig

                connect_config = {
                    "namespace": settings.temporal_namespace,
                }

                # Add TLS for Temporal Cloud
                if settings.temporal_api_key:
                    connect_config["tls"] = TLSConfig()
                    connect_config["api_key"] = settings.temporal_api_key

                self.temporal_client = await TemporalClient.connect(
                    settings.temporal_address,
                    data_converter=pydantic_data_converter,
                    **connect_config
                )
                logger.info("Temporal connected", address=settings.temporal_address)

            # Supabase
            if settings.supabase_url and settings.supabase_key:
                self.supabase_client = create_client(
                    settings.supabase_url, settings.supabase_key
                )
                logger.info("Supabase connected", url=settings.supabase_url)

        except Exception as e:
            logger.warning("Error initializing connections", error=str(e))
            # Don't fail hard, allow partial connections

    async def close_connections(self):
        """Close database connections"""
        try:
            if self.neo4j_driver:
                await self.neo4j_driver.close()
            if self.weaviate_client:
                self.weaviate_client.close()
            if self.temporal_client:
                await self.temporal_client.close()
        except Exception as e:
            print(f"Error closing connections: {e}")

    # Query resolvers
    async def get_domain(self, domain_id: str) -> Domain | None:
        """Get a single domain by ID"""
        async with self.neo4j_driver.session() as session:
            result = await session.run(
                """
                MATCH (d:Domain {domain_id: $domain_id})
                OPTIONAL MATCH (d)-[:CONTAINS]->(doc:Document)
                OPTIONAL MATCH (d)-[:HAS_ENTITY]->(e:Entity)
                OPTIONAL MATCH (e)-[r:RELATES_TO]->()
                RETURN d,
                       COUNT(DISTINCT doc) as doc_count,
                       COUNT(DISTINCT e) as entity_count,
                       COUNT(DISTINCT r) as rel_count
                """,
                domain_id=domain_id,
            )
            record = await result.single()
            if record:
                d = record["d"]
                # Handle Neo4j datetime format
                created_at = d.get("created_at")
                updated_at = d.get("updated_at")

                # Convert Neo4j datetime to Python datetime
                if created_at and isinstance(created_at, str):
                    created_at = (
                        datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        if created_at
                        else datetime.now()
                    )
                elif not created_at:
                    created_at = datetime.now()

                if updated_at and isinstance(updated_at, str):
                    updated_at = (
                        datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                        if updated_at
                        else datetime.now()
                    )
                elif not updated_at:
                    updated_at = datetime.now()

                return Domain(
                    domainId=d["domain_id"],
                    name=d["name"],
                    description=d.get("description"),
                    createdBy=d["created_by"],
                    createdAt=created_at,
                    updatedAt=updated_at,
                    documentCount=record["doc_count"],
                    entityCount=record["entity_count"],
                    relationshipCount=record["rel_count"],
                )
        return None

    async def list_domains(self, created_by: str | None = None) -> list[Domain]:
        """List all domains, optionally filtered by creator"""
        async with self.neo4j_driver.session() as session:
            query = """
                MATCH (d:Domain)
                WHERE $created_by IS NULL OR d.created_by = $created_by
                OPTIONAL MATCH (d)-[:CONTAINS]->(doc:Document)
                OPTIONAL MATCH (d)-[:HAS_ENTITY]->(e:Entity)
                OPTIONAL MATCH (e)-[r:RELATES_TO]->()
                RETURN d,
                       COUNT(DISTINCT doc) as doc_count,
                       COUNT(DISTINCT e) as entity_count,
                       COUNT(DISTINCT r) as rel_count
                ORDER BY d.created_at DESC
            """
            result = await session.run(query, created_by=created_by)

            domains = []
            async for record in result:
                d = record["d"]
                # Handle Neo4j datetime format
                created_at = d.get("created_at")
                updated_at = d.get("updated_at")

                # Convert Neo4j datetime to Python datetime
                if created_at and isinstance(created_at, str):
                    created_at = (
                        datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        if created_at
                        else datetime.now()
                    )
                elif not created_at:
                    created_at = datetime.now()

                if updated_at and isinstance(updated_at, str):
                    updated_at = (
                        datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                        if updated_at
                        else datetime.now()
                    )
                elif not updated_at:
                    updated_at = datetime.now()

                domains.append(
                    Domain(
                        domain_id=d["domain_id"],
                        name=d["name"],
                        description=d.get("description"),
                        created_by=d["created_by"],
                        created_at=created_at,
                        updated_at=updated_at,
                        document_count=record["doc_count"],
                        entity_count=record["entity_count"],
                        relationship_count=record["rel_count"],
                    )
                )
            return domains

    async def search_domains(
        self, query: str, user_id: str | None = None, limit: int = 10
    ) -> SearchResponse:
        """Semantic search across domains using vector and graph"""
        start_time = datetime.now()

        # Vector search in Weaviate
        vector_results = []
        try:
            where_filter = None
            if user_id:
                where_filter = {
                    "path": ["created_by"],
                    "operator": "Equal",
                    "valueString": user_id,
                }

            result = (
                self.weaviate_client.query.get(
                    "Domain", ["domain_id", "name", "description"]
                )
                .with_near_text({"concepts": [query]})
                .with_where(where_filter)
                .with_limit(limit)
                .with_additional(["score", "explain"])
                .do()
            )

            if (
                "data" in result
                and "Get" in result["data"]
                and "Domain" in result["data"]["Get"]
            ):
                for item in result["data"]["Get"]["Domain"]:
                    vector_results.append(
                        SearchResult(
                            domainId=item["domain_id"],
                            domainName=item["name"],
                            description=item.get("description"),
                            score=item["_additional"].get("score", 0.0),
                            source="vector",
                            highlights=[],
                        )
                    )
        except Exception as e:
            print(f"Vector search error: {e}")

        # Graph search in Neo4j
        graph_results = []
        async with self.neo4j_driver.session() as session:
            cypher_query = """
                CALL db.index.fulltext.queryNodes('domain_search', $search_query)
                YIELD node, score
                WHERE $user_id IS NULL OR node.created_by = $user_id
                RETURN node, score
                ORDER BY score DESC
                LIMIT $limit
            """
            result = await session.run(
                cypher_query, search_query=query, user_id=user_id, limit=limit
            )

            async for record in result:
                node = record["node"]
                graph_results.append(
                    SearchResult(
                        domainId=node["domain_id"],
                        domainName=node["name"],
                        description=node.get("description"),
                        score=record["score"],
                        source="graph",
                        highlights=[],
                    )
                )

        elapsed = (datetime.now() - start_time).total_seconds() * 1000

        return SearchResponse(
            query=query,
            vectorResults=vector_results,
            graphResults=graph_results,
            totalResults=len(vector_results) + len(graph_results),
            searchTimeMs=elapsed,
        )

    async def get_knowledge_graph(
        self, domain_id: str, max_nodes: int = 100
    ) -> KnowledgeGraph:
        """Get knowledge graph for visualization"""
        async with self.neo4j_driver.session() as session:
            # Get nodes
            nodes_query = """
                MATCH (d:Domain {domain_id: $domain_id})-[:HAS_ENTITY]->(e:Entity)
                OPTIONAL MATCH (e)-[r:RELATES_TO]->()
                WITH e, COUNT(r) as connections
                RETURN e, connections
                ORDER BY connections DESC
                LIMIT $max_nodes
            """
            nodes_result = await session.run(
                nodes_query, domain_id=domain_id, max_nodes=max_nodes
            )

            nodes = []
            node_ids = set()
            async for record in nodes_result:
                e = record["e"]
                node_ids.add(e["entity_id"])
                nodes.append(
                    KnowledgeGraphNode(
                        id=e["entity_id"],
                        label=e["name"],
                        type=e["entity_type"],
                        properties=json.dumps(e.get("properties", {})),
                        connections=record["connections"],
                    )
                )

            # Get edges between these nodes
            edges = []
            if node_ids:
                edges_query = """
                    MATCH (e1:Entity)-[r:RELATES_TO]->(e2:Entity)
                    WHERE e1.entity_id IN $node_ids AND e2.entity_id IN $node_ids
                    RETURN e1.entity_id as source, e2.entity_id as target,
                           r.relationship_type as type, r
                """
                edges_result = await session.run(edges_query, node_ids=list(node_ids))

                async for record in edges_result:
                    r = record["r"]
                    edges.append(
                        KnowledgeGraphEdge(
                            source=record["source"],
                            target=record["target"],
                            type=record["type"],
                            label=record["type"],
                            properties=json.dumps(r.get("properties", {})),
                        )
                    )

            return KnowledgeGraph(
                domainId=domain_id,
                nodes=nodes,
                edges=edges,
                nodeCount=len(nodes),
                edgeCount=len(edges),
            )

    async def get_domain_stats(self, domain_id: str) -> DomainStats | None:
        """Get comprehensive statistics for a domain"""
        async with self.neo4j_driver.session() as session:
            stats_query = """
                MATCH (d:Domain {domain_id: $domain_id})
                OPTIONAL MATCH (d)-[:CONTAINS]->(doc:Document)
                OPTIONAL MATCH (d)-[:HAS_ENTITY]->(e:Entity)
                OPTIONAL MATCH (e)-[r:RELATES_TO]->()
                OPTIONAL MATCH (d)-[:HAS_QUESTION]->(q:Question)
                WITH d,
                     COUNT(DISTINCT doc) as doc_count,
                     COUNT(DISTINCT e) as entity_count,
                     COUNT(DISTINCT r) as rel_count,
                     COUNT(DISTINCT q) as question_count,
                     COLLECT(DISTINCT e.entity_type) as entity_types,
                     COLLECT(DISTINCT r.relationship_type) as rel_types,
                     AVG(q.confidence) as avg_confidence,
                     MAX(d.updated_at) as last_activity
                RETURN d, doc_count, entity_count, rel_count, question_count,
                       entity_types[0..5] as top_entities,
                       rel_types[0..5] as top_relations,
                       avg_confidence, last_activity
            """
            result = await session.run(stats_query, domain_id=domain_id)
            record = await result.single()

            if record:
                return DomainStats(
                    domainId=domain_id,
                    totalDocuments=record["doc_count"],
                    totalEntities=record["entity_count"],
                    totalRelationships=record["rel_count"],
                    totalQuestions=record["question_count"],
                    avgConfidence=record["avg_confidence"] or 0.0,
                    lastActivity=datetime.fromisoformat(record["last_activity"]),
                    topEntityTypes=record["top_entities"] or [],
                    topRelationshipTypes=record["top_relations"] or [],
                )
        return None

    async def get_workflow_status(self, workflow_id: str) -> WorkflowInfo | None:
        """Get workflow status from Temporal"""
        try:
            handle = self.temporal_client.get_workflow_handle(workflow_id)
            description = await handle.describe()

            status = WorkflowStatus.RUNNING
            if description.status == "COMPLETED":
                status = WorkflowStatus.COMPLETED
            elif description.status == "FAILED":
                status = WorkflowStatus.FAILED
            elif description.status == "TERMINATED":
                status = WorkflowStatus.TERMINATED
            elif description.status == "CANCELED":
                status = WorkflowStatus.CANCELED

            return WorkflowInfo(
                workflowId=workflow_id,
                workflowType=description.type_name,
                status=status,
                startedAt=description.start_time,
                completedAt=description.close_time,
                error=(
                    description.failure_info.message
                    if description.failure_info
                    else None
                ),
            )
        except Exception:
            return None


# Global resolver instance
resolver = GraphQLResolvers()

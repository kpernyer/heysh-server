"""GraphQL schema definition"""

import strawberry

from .resolvers import resolver
from .types import (
    AskQuestionInput,
    CreateDomainInput,
    Document,
    Domain,
    DomainStats,
    Entity,
    KnowledgeGraph,
    Question,
    Relationship,
    SearchResponse,
    UploadDocumentInput,
    WorkflowInfo,
)


@strawberry.type
class Query:
    """GraphQL Query root"""

    @strawberry.field
    async def domain(self, domain_id: str) -> Domain | None:
        """Get a single domain by ID"""
        return await resolver.get_domain(domain_id)

    @strawberry.field
    async def domains(self, created_by: str | None = None) -> list[Domain]:
        """List all domains, optionally filtered by creator"""
        return await resolver.list_domains(created_by)

    @strawberry.field
    async def search_domains(
        self, query: str, user_id: str | None = None, limit: int = 10
    ) -> SearchResponse:
        """Semantic search across domains using both vector and graph search.
        Returns results from both Weaviate (vector) and Neo4j (graph).
        """
        return await resolver.search_domains(query, user_id, limit)

    @strawberry.field
    async def knowledge_graph(
        self, domain_id: str, max_nodes: int = 100
    ) -> KnowledgeGraph:
        """Get knowledge graph for a domain, suitable for visualization.
        Includes nodes (entities) and edges (relationships).
        """
        return await resolver.get_knowledge_graph(domain_id, max_nodes)

    @strawberry.field
    async def domain_stats(self, domain_id: str) -> DomainStats | None:
        """Get comprehensive statistics for a domain"""
        return await resolver.get_domain_stats(domain_id)

    @strawberry.field
    async def workflow_status(self, workflow_id: str) -> WorkflowInfo | None:
        """Get the status of a workflow execution"""
        return await resolver.get_workflow_status(workflow_id)

    @strawberry.field
    async def domain_documents(self, domain_id: str, limit: int = 50) -> list[Document]:
        """Get documents in a domain"""
        # Implementation would fetch from Neo4j
        # This is a placeholder for now
        return []

    @strawberry.field
    async def domain_entities(
        self, domain_id: str, entity_type: str | None = None, limit: int = 100
    ) -> list[Entity]:
        """Get entities in a domain, optionally filtered by type"""
        # Implementation would fetch from Neo4j
        # This is a placeholder for now
        return []

    @strawberry.field
    async def domain_relationships(
        self, domain_id: str, relationship_type: str | None = None, limit: int = 100
    ) -> list[Relationship]:
        """Get relationships in a domain, optionally filtered by type"""
        # Implementation would fetch from Neo4j
        # This is a placeholder for now
        return []

    @strawberry.field
    async def domain_questions(
        self, domain_id: str, user_id: str | None = None, limit: int = 50
    ) -> list[Question]:
        """Get questions asked in a domain"""
        # Implementation would fetch from database
        # This is a placeholder for now
        return []


@strawberry.type
class Mutation:
    """GraphQL Mutation root"""

    @strawberry.mutation
    async def create_domain(self, input: CreateDomainInput) -> Domain:
        """Create a new knowledge domain"""
        import uuid
        from datetime import datetime

        # This would typically call the actual backend service
        # For now, returning a mock response
        return Domain(
            domain_id=str(uuid.uuid4()),
            name=input.name,
            description=input.description,
            created_by=input.created_by,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            document_count=0,
            entity_count=0,
            relationship_count=0,
        )

    @strawberry.mutation
    async def upload_document(self, input: UploadDocumentInput) -> WorkflowInfo:
        """Upload a document to a domain and start processing workflow"""
        import uuid
        from datetime import datetime

        from .types import WorkflowStatus

        # This would typically call the Temporal workflow
        # For now, returning a mock response
        return WorkflowInfo(
            workflow_id=str(uuid.uuid4()),
            workflow_type="DocumentProcessingWorkflow",
            status=WorkflowStatus.RUNNING,
            started_at=datetime.now(),
            input_data=str(input),
        )

    @strawberry.mutation
    async def ask_question(self, input: AskQuestionInput) -> WorkflowInfo:
        """Ask a question in a domain context"""
        import uuid
        from datetime import datetime

        from .types import WorkflowStatus

        # This would typically call the Temporal workflow
        # For now, returning a mock response
        return WorkflowInfo(
            workflow_id=str(uuid.uuid4()),
            workflow_type="QuestionAnsweringWorkflow",
            status=WorkflowStatus.RUNNING,
            started_at=datetime.now(),
            input_data=str(input),
        )


@strawberry.type
class Subscription:
    """GraphQL Subscription root for real-time updates"""

    @strawberry.subscription
    async def workflow_updates(self, workflow_id: str) -> WorkflowInfo:
        """Subscribe to workflow status updates"""
        # This would implement WebSocket-based updates
        # Placeholder for now
        import asyncio
        from datetime import datetime

        from .types import WorkflowStatus

        # Simulate updates
        for i in range(3):
            await asyncio.sleep(2)
            yield WorkflowInfo(
                workflow_id=workflow_id,
                workflow_type="DocumentProcessingWorkflow",
                status=WorkflowStatus.RUNNING if i < 2 else WorkflowStatus.COMPLETED,
                started_at=datetime.now(),
            )


# Create the GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)

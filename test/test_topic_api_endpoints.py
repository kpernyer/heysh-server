"""Tests for updated Topic API endpoints (formerly Domain)."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from src.service.api import app

client = TestClient(app)


class TestCoreEndpoints:
    """Test cases for core API endpoints."""

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hey.sh Backend API"
        assert data["version"] == "0.1.0"


class TestTopicEndpoints:
    """Test cases for topic endpoints (formerly domain endpoints)."""

    def test_list_topics_success(self):
        """Test successful topic listing."""
        mock_topics = [
            {
                "id": "topic1",
                "name": "Machine Learning",
                "description": "ML and AI topics",
                "created_by": "user123"
            },
            {
                "id": "topic2",
                "name": "Web Development",
                "description": "Frontend and backend development",
                "created_by": "user123"
            }
        ]

        with patch('src.app.clients.supabase.get_supabase_client') as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client

            mock_response = Mock()
            mock_response.data = mock_topics
            mock_client.table.return_value.select.return_value.execute.return_value = mock_response

            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.get("/api/v1/topics")

                assert response.status_code == 200
                data = response.json()
                assert "topics" in data
                assert len(data["topics"]) == 2
                assert data["count"] == 2
                assert data["topics"][0]["name"] == "Machine Learning"

    def test_get_topic_success(self):
        """Test successful topic retrieval by ID."""
        mock_topic = {
            "id": "topic123",
            "name": "Data Science",
            "description": "Data analysis and statistics",
            "created_by": "user123",
            "created_at": "2025-01-28T10:00:00Z"
        }

        with patch('src.app.clients.supabase.get_supabase_client') as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client

            mock_response = Mock()
            mock_response.data = mock_topic
            mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response

            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.get("/api/v1/topics/topic123")

                assert response.status_code == 200
                data = response.json()
                assert data["id"] == "topic123"
                assert data["name"] == "Data Science"

    def test_search_topics_success(self):
        """Test successful topic search."""
        mock_search_results = {
            "vector_results": [
                {
                    "id": "topic1",
                    "name": "Machine Learning",
                    "description": "ML fundamentals",
                    "score": 0.95
                }
            ],
            "graph_results": [
                {
                    "id": "topic2",
                    "name": "Deep Learning",
                    "description": "Neural networks",
                    "is_member": True
                }
            ]
        }

        with patch('activity.domain.search_domains_activity', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_search_results

            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.get("/api/v1/topics/search?q=machine+learning&user_id=user123&use_llm=false")

                assert response.status_code == 200
                data = response.json()
                assert "results" in data
                assert "result_count" in data
                assert data["result_count"]["vector"] == 1
                assert data["result_count"]["graph"] == 1


class TestDocumentEndpointsWithTopics:
    """Test cases for document endpoints using topic_id."""

    def test_upload_document_with_topic_id(self):
        """Test document upload with topic_id (not domain_id)."""
        mock_handle = Mock()
        mock_handle.id = "workflow-doc-123"

        with patch('src.service.routes_workflows.temporal_client') as mock_temporal:
            mock_temporal.start_workflow.return_value = mock_handle

            response = client.post(
                "/api/v1/documents",
                json={
                    "document_id": "doc123",
                    "topic_id": "topic456",  # Using topic_id
                    "file_path": "topic-456/document-123.pdf"
                }
            )

            assert response.status_code == 202
            data = response.json()
            assert data["workflow_id"] == "workflow-doc-123"
            assert data["status"] == "processing"
            assert "Document processing started" in data["message"]

    def test_list_documents_filtered_by_topic(self):
        """Test listing documents filtered by topic_id."""
        mock_documents = [
            {
                "id": "doc1",
                "topic_id": "topic123",
                "name": "Document 1",
                "status": "processed"
            }
        ]

        with patch('src.app.clients.supabase.get_supabase_client') as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client

            mock_response = Mock()
            mock_response.data = mock_documents

            mock_table = Mock()
            mock_select = Mock()
            mock_eq = Mock()

            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_response

            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.get("/api/v1/documents?topic_id=topic123")

                assert response.status_code == 200
                data = response.json()
                assert "documents" in data
                assert data["count"] == 1


class TestQuestionEndpointsWithTopics:
    """Test cases for question endpoints using topic_id."""

    def test_ask_question_with_topic_id(self):
        """Test asking question with topic_id."""
        mock_handle = Mock()
        mock_handle.id = "workflow-question-456"

        with patch('src.service.routes_workflows.temporal_client') as mock_temporal:
            mock_temporal.start_workflow.return_value = mock_handle

            response = client.post(
                "/api/v1/questions",
                json={
                    "question_id": "q123",
                    "question": "What is machine learning?",
                    "topic_id": "topic789",  # Using topic_id
                    "user_id": "user123"
                }
            )

            assert response.status_code == 202
            data = response.json()
            assert data["workflow_id"] == "workflow-question-456"
            assert data["status"] == "processing"
            assert "Question answering started" in data["message"]

    def test_ask_question_validation_error(self):
        """Test question with invalid data."""
        response = client.post(
            "/api/v1/questions",
            json={
                "question_id": "q123",
                "question": "short",  # Too short - min_length is 10
                "topic_id": "topic789",
                "user_id": "user123"
            }
        )

        assert response.status_code == 422  # Validation error


class TestWorkflowEndpointsWithTopics:
    """Test cases for workflow endpoints using topic_id."""

    def test_create_workflow_with_topic_id(self):
        """Test creating workflow with topic_id."""
        mock_workflow = {
            "id": "workflow123",
            "name": "Test Workflow",
            "topic_id": "topic456",
            "status": "active"
        }

        with patch('src.service.models.WorkflowModel.create_workflow', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_workflow

            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.post(
                    "/api/v1/workflows",
                    json={
                        "name": "Test Workflow",
                        "topic_id": "topic456",  # Using topic_id
                        "yaml_definition": {"version": "1.0", "steps": []},
                        "description": "A test workflow",
                        "is_active": True
                    }
                )

                assert response.status_code == 201
                data = response.json()
                assert data["id"] == "workflow123"
                assert data["topic_id"] == "topic456"

    def test_list_workflows_filtered_by_topic(self):
        """Test listing workflows filtered by topic_id."""
        mock_workflows = [
            {
                "id": "wf1",
                "name": "Workflow 1",
                "topic_id": "topic123",
                "status": "completed"
            }
        ]

        with patch('src.service.models.WorkflowModel.get_by_domain', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_workflows

            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.get("/api/v1/workflows?topic_id=topic123")

                assert response.status_code == 200
                data = response.json()
                assert "workflows" in data
                assert data["count"] == 1
                assert data["workflows"][0]["topic_id"] == "topic123"

    def test_get_workflow_status(self):
        """Test getting workflow status."""
        mock_result = Mock()
        mock_result.status.name = "RUNNING"
        mock_result.workflow_type = "DocumentProcessingWorkflow"

        with patch('src.service.routes_workflows.temporal_client') as mock_temporal:
            mock_handle = Mock()
            mock_handle.describe.return_value = mock_result
            mock_temporal.get_workflow_handle.return_value = mock_handle

            response = client.get("/api/v1/workflows/workflow123/status")

            assert response.status_code == 200
            data = response.json()
            assert data["workflow_id"] == "workflow123"
            assert data["status"] == "RUNNING"
            assert data["type"] == "DocumentProcessingWorkflow"


class TestCreateTopicEndpoint:
    """Test cases for creating topics."""

    def test_create_topic_success(self):
        """Test successful topic creation."""
        with patch('activity.domain.index_domain_activity', new_callable=AsyncMock) as mock_index:
            mock_index.return_value = {
                "topic_id": "topic123",
                "status": "indexed"
            }

            response = client.post(
                "/api/v1/topics",
                json={
                    "topic_id": "topic123",
                    "name": "Artificial Intelligence",
                    "description": "AI and machine learning topics",
                    "created_by": "user456"
                }
            )

            assert response.status_code == 201
            data = response.json()
            assert data["topic_id"] == "topic123"
            assert data["name"] == "Artificial Intelligence"
            assert data["status"] == "indexed"
            assert "successfully" in data["message"].lower()

    def test_create_topic_missing_fields(self):
        """Test topic creation with missing required fields."""
        response = client.post(
            "/api/v1/topics",
            json={
                "topic_id": "topic123",
                "name": "Test Topic"
                # Missing created_by field
            }
        )

        assert response.status_code == 422  # Validation error


class TestReviewEndpointsWithTopics:
    """Test cases for review endpoints using topic_id."""

    def test_submit_review_with_topic_id(self):
        """Test submitting review with topic_id."""
        mock_handle = Mock()
        mock_handle.id = "workflow-review-789"

        with patch('src.service.routes_workflows.temporal_client') as mock_temporal:
            mock_temporal.start_workflow.return_value = mock_handle

            response = client.post(
                "/api/v1/reviews",
                json={
                    "review_id": "review123",
                    "reviewable_type": "document",
                    "reviewable_id": "doc456",
                    "topic_id": "topic789"  # Using topic_id
                }
            )

            assert response.status_code == 202
            data = response.json()
            assert data["workflow_id"] == "workflow-review-789"
            assert data["status"] == "processing"


class TestSchemaValidation:
    """Test schema validation for updated models."""

    def test_document_request_requires_topic_id(self):
        """Test that document request requires topic_id field."""
        response = client.post(
            "/api/v1/documents",
            json={
                "document_id": "doc123",
                "domain_id": "domain456",  # Old field name - should fail
                "file_path": "test.pdf"
            }
        )

        # Should fail validation because topic_id is required
        assert response.status_code == 422

    def test_question_request_requires_topic_id(self):
        """Test that question request requires topic_id field."""
        response = client.post(
            "/api/v1/questions",
            json={
                "question_id": "q123",
                "question": "What is the answer to everything?",
                "domain_id": "domain456",  # Old field name - should fail
                "user_id": "user123"
            }
        )

        # Should fail validation because topic_id is required
        assert response.status_code == 422


@pytest.mark.integration
class TestEndToEndTopicFlow:
    """Integration test for complete topic workflow."""

    def test_create_topic_upload_document_ask_question(self):
        """Test complete flow: create topic -> upload document -> ask question."""

        # Step 1: Create topic
        with patch('activity.domain.index_domain_activity', new_callable=AsyncMock) as mock_index:
            mock_index.return_value = {"topic_id": "topic123", "status": "indexed"}

            response = client.post(
                "/api/v1/topics",
                json={
                    "topic_id": "topic123",
                    "name": "Test Topic",
                    "description": "Testing",
                    "created_by": "user123"
                }
            )

            assert response.status_code == 201
            topic_id = response.json()["topic_id"]

        # Step 2: Upload document to topic
        mock_handle = Mock()
        mock_handle.id = "workflow-doc-123"

        with patch('src.service.routes_workflows.temporal_client') as mock_temporal:
            mock_temporal.start_workflow.return_value = mock_handle

            response = client.post(
                "/api/v1/documents",
                json={
                    "document_id": "doc123",
                    "topic_id": topic_id,
                    "file_path": "test.pdf"
                }
            )

            assert response.status_code == 202
            doc_workflow_id = response.json()["workflow_id"]

        # Step 3: Ask question about the topic
        mock_handle2 = Mock()
        mock_handle2.id = "workflow-question-456"

        with patch('src.service.routes_workflows.temporal_client') as mock_temporal:
            mock_temporal.start_workflow.return_value = mock_handle2

            response = client.post(
                "/api/v1/questions",
                json={
                    "question_id": "q123",
                    "question": "What does this document say?",
                    "topic_id": topic_id,
                    "user_id": "user123"
                }
            )

            assert response.status_code == 202
            question_workflow_id = response.json()["workflow_id"]

        # Verify all workflows were created
        assert doc_workflow_id == "workflow-doc-123"
        assert question_workflow_id == "workflow-question-456"

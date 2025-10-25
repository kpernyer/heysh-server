"""Tests for core API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

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

    def test_backend_info_endpoint(self):
        """Test backend info endpoint."""
        with patch('src.service.version.get_backend_info') as mock_info:
            mock_info.return_value = {
                "version": "0.1.0",
                "environment": "development",
                "commit": "abc123",
                "timestamp": "2023-01-01T00:00:00Z"
            }
            
            response = client.get("/api/v1/info")
            assert response.status_code == 200
            data = response.json()
            assert data["version"] == "0.1.0"
            assert data["environment"] == "development"

    def test_cors_headers(self):
        """Test CORS headers are set correctly."""
        response = client.options("/health")
        # CORS preflight should be handled by middleware
        assert response.status_code in [200, 204]


class TestDocumentEndpoints:
    """Test cases for document endpoints."""

    def test_upload_document_success(self):
        """Test successful document upload."""
        mock_workflow_response = {
            "workflow_id": "workflow123",
            "status": "started",
            "message": "Document processing started"
        }
        
        with patch('src.service.routes_workflows.temporal_client') as mock_temporal:
            mock_temporal.start_workflow.return_value = "workflow123"
            
            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.post(
                    "/api/v1/documents",
                    json={
                        "domain_id": "domain123",
                        "file_name": "test.pdf",
                        "file_content": "base64encodedcontent",
                        "file_type": "application/pdf"
                    }
                )
                
                assert response.status_code == 202
                data = response.json()
                assert "workflow_id" in data
                assert data["status"] == "started"

    def test_list_documents_success(self):
        """Test successful document listing."""
        mock_documents = [
            {
                "id": "doc1",
                "domain_id": "domain123",
                "file_name": "test1.pdf",
                "status": "processed"
            },
            {
                "id": "doc2", 
                "domain_id": "domain123",
                "file_name": "test2.pdf",
                "status": "processing"
            }
        ]
        
        with patch('src.service.models.document_model.DocumentModel.get_by_domain', return_value=mock_documents):
            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.get("/api/v1/documents?domain_id=domain123")
                
                assert response.status_code == 200
                data = response.json()
                assert "documents" in data
                assert len(data["documents"]) == 2
                assert data["count"] == 2

    def test_get_document_success(self):
        """Test successful document retrieval."""
        mock_document = {
            "id": "doc123",
            "domain_id": "domain123",
            "file_name": "test.pdf",
            "status": "processed",
            "created_at": "2023-01-01T00:00:00Z"
        }
        
        with patch('src.service.models.document_model.DocumentModel.get_by_id', return_value=mock_document):
            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.get("/api/v1/documents/doc123")
                
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == "doc123"
                assert data["file_name"] == "test.pdf"

    def test_get_document_not_found(self):
        """Test document not found."""
        with patch('src.service.models.document_model.DocumentModel.get_by_id', return_value=None):
            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.get("/api/v1/documents/nonexistent")
                
                assert response.status_code == 404
                assert "Document not found" in response.json()["detail"]


class TestQuestionEndpoints:
    """Test cases for question endpoints."""

    def test_ask_question_success(self):
        """Test successful question asking."""
        with patch('src.service.routes_workflows.temporal_client') as mock_temporal:
            mock_temporal.start_workflow.return_value = "workflow123"
            
            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.post(
                    "/api/v1/questions",
                    json={
                        "domain_id": "domain123",
                        "question": "What is the main topic?",
                        "context": "I need to understand this document"
                    }
                )
                
                assert response.status_code == 202
                data = response.json()
                assert "workflow_id" in data
                assert data["status"] == "started"

    def test_ask_question_missing_fields(self):
        """Test question asking with missing required fields."""
        with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
            response = client.post(
                "/api/v1/questions",
                json={
                    "domain_id": "domain123"
                    # Missing question field
                }
            )
            
            assert response.status_code == 422  # Validation error


class TestWorkflowEndpoints:
    """Test cases for workflow endpoints."""

    def test_list_workflows_success(self):
        """Test successful workflow listing."""
        mock_workflows = [
            {
                "id": "workflow1",
                "domain_id": "domain123",
                "status": "completed",
                "type": "document_processing"
            }
        ]
        
        with patch('src.service.models.workflow_model.WorkflowModel.get_by_domain', return_value=mock_workflows):
            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.get("/api/v1/workflows?domain_id=domain123")
                
                assert response.status_code == 200
                data = response.json()
                assert "workflows" in data
                assert len(data["workflows"]) == 1
                assert data["count"] == 1

    def test_get_workflow_success(self):
        """Test successful workflow retrieval."""
        mock_workflow = {
            "id": "workflow123",
            "domain_id": "domain123",
            "status": "running",
            "type": "document_processing",
            "created_at": "2023-01-01T00:00:00Z"
        }
        
        with patch('src.service.models.workflow_model.WorkflowModel.get_by_id', return_value=mock_workflow):
            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.get("/api/v1/workflows/workflow123")
                
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == "workflow123"
                assert data["status"] == "running"

    def test_get_workflow_results_success(self):
        """Test successful workflow results retrieval."""
        mock_results = {
            "workflow_id": "workflow123",
            "status": "completed",
            "results": {
                "summary": "Document processed successfully",
                "entities": ["entity1", "entity2"],
                "relationships": [{"from": "entity1", "to": "entity2", "type": "related"}]
            }
        }
        
        with patch('src.service.models.workflow_model.WorkflowModel.get_results', return_value=mock_results):
            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.get("/api/v1/workflows/workflow123/results")
                
                assert response.status_code == 200
                data = response.json()
                assert data["workflow_id"] == "workflow123"
                assert data["status"] == "completed"
                assert "results" in data


class TestDomainEndpoints:
    """Test cases for domain endpoints."""

    def test_list_domains_success(self):
        """Test successful domain listing."""
        mock_domains = [
            {
                "id": "domain1",
                "name": "Domain 1",
                "description": "Test domain 1",
                "owner_id": "user123"
            }
        ]
        
        with patch('src.app.clients.supabase.get_supabase_client') as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            
            mock_response = Mock()
            mock_response.data = mock_domains
            mock_client.table.return_value.select.return_value.execute.return_value = mock_response
            
            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.get("/api/v1/domains")
                
                assert response.status_code == 200
                data = response.json()
                assert "domains" in data
                assert len(data["domains"]) == 1
                assert data["count"] == 1

    def test_search_domains_success(self):
        """Test successful domain search."""
        mock_search_results = {
            "domains": [
                {
                    "id": "domain1",
                    "name": "Test Domain",
                    "description": "A test domain",
                    "relevance_score": 0.95
                }
            ],
            "total_count": 1
        }
        
        with patch('src.service.routes_data.search_domains', return_value=mock_search_results):
            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.get("/api/v1/domains/search?q=test&user_id=user123&use_llm=true")
                
                assert response.status_code == 200
                data = response.json()
                assert "domains" in data
                assert len(data["domains"]) == 1
                assert data["total_count"] == 1

    def test_get_domain_success(self):
        """Test successful domain retrieval."""
        mock_domain = {
            "id": "domain123",
            "name": "Test Domain",
            "description": "A test domain",
            "owner_id": "user123",
            "created_at": "2023-01-01T00:00:00Z"
        }
        
        with patch('src.app.clients.supabase.get_supabase_client') as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            
            mock_response = Mock()
            mock_response.data = [mock_domain]
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            
            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.get("/api/v1/domains/domain123")
                
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == "domain123"
                assert data["name"] == "Test Domain"

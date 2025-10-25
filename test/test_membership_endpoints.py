"""Tests for membership management endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from src.service.api import app

client = TestClient(app)


class TestMembershipEndpoints:
    """Test cases for membership management endpoints."""

    def test_create_membership_request_success(self):
        """Test successful membership request creation."""
        mock_domain = {
            "id": "domain123",
            "name": "Test Domain"
        }
        
        mock_request = {
            "id": "request123",
            "user_id": "user123",
            "domain_id": "domain123",
            "status": "pending",
            "message": "Please accept me",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }
        
        with patch('src.app.clients.supabase.get_supabase_client') as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            
            # Mock domain exists check
            mock_domain_response = Mock()
            mock_domain_response.data = [mock_domain]
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_domain_response
            
            # Mock no existing membership
            mock_member_response = Mock()
            mock_member_response.data = []
            mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_member_response
            
            # Mock no existing request
            mock_request_response = Mock()
            mock_request_response.data = []
            mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = mock_request_response
            
            # Mock successful creation
            mock_create_response = Mock()
            mock_create_response.data = [mock_request]
            mock_client.table.return_value.insert.return_value.execute.return_value = mock_create_response
            
            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.post(
                    "/api/v1/membership-requests/",
                    json={
                        "domain_id": "domain123",
                        "message": "Please accept me"
                    }
                )
                
                assert response.status_code == 201
                data = response.json()
                assert data["id"] == "request123"
                assert data["user_id"] == "user123"
                assert data["domain_id"] == "domain123"
                assert data["status"] == "pending"
                assert data["message"] == "Please accept me"

    def test_create_membership_request_domain_not_found(self):
        """Test membership request creation with non-existent domain."""
        with patch('src.app.clients.supabase.get_supabase_client') as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            
            # Mock domain not found
            mock_domain_response = Mock()
            mock_domain_response.data = []
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_domain_response
            
            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.post(
                    "/api/v1/membership-requests/",
                    json={
                        "domain_id": "nonexistent",
                        "message": "Please accept me"
                    }
                )
                
                assert response.status_code == 404
                assert "Domain not found" in response.json()["detail"]

    def test_create_membership_request_already_member(self):
        """Test membership request creation when user is already a member."""
        mock_domain = {
            "id": "domain123",
            "name": "Test Domain"
        }
        
        with patch('src.app.clients.supabase.get_supabase_client') as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            
            # Mock domain exists
            mock_domain_response = Mock()
            mock_domain_response.data = [mock_domain]
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_domain_response
            
            # Mock user is already a member
            mock_member_response = Mock()
            mock_member_response.data = [{"id": "member123"}]
            mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_member_response
            
            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.post(
                    "/api/v1/membership-requests/",
                    json={
                        "domain_id": "domain123",
                        "message": "Please accept me"
                    }
                )
                
                assert response.status_code == 409
                assert "already a member" in response.json()["detail"]

    def test_create_membership_request_pending_exists(self):
        """Test membership request creation when pending request already exists."""
        mock_domain = {
            "id": "domain123",
            "name": "Test Domain"
        }
        
        with patch('src.app.clients.supabase.get_supabase_client') as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            
            # Mock domain exists
            mock_domain_response = Mock()
            mock_domain_response.data = [mock_domain]
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_domain_response
            
            # Mock no existing membership
            mock_member_response = Mock()
            mock_member_response.data = []
            mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_member_response
            
            # Mock pending request exists
            mock_request_response = Mock()
            mock_request_response.data = [{"id": "existing_request"}]
            mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = mock_request_response
            
            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.post(
                    "/api/v1/membership-requests/",
                    json={
                        "domain_id": "domain123",
                        "message": "Please accept me"
                    }
                )
                
                assert response.status_code == 409
                assert "pending membership request already exists" in response.json()["detail"]

    def test_create_membership_request_no_message(self):
        """Test membership request creation without message."""
        mock_domain = {
            "id": "domain123",
            "name": "Test Domain"
        }
        
        mock_request = {
            "id": "request123",
            "user_id": "user123",
            "domain_id": "domain123",
            "status": "pending",
            "message": None,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }
        
        with patch('src.app.clients.supabase.get_supabase_client') as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            
            # Mock domain exists
            mock_domain_response = Mock()
            mock_domain_response.data = [mock_domain]
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_domain_response
            
            # Mock no existing membership
            mock_member_response = Mock()
            mock_member_response.data = []
            mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_member_response
            
            # Mock no existing request
            mock_request_response = Mock()
            mock_request_response.data = []
            mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = mock_request_response
            
            # Mock successful creation
            mock_create_response = Mock()
            mock_create_response.data = [mock_request]
            mock_client.table.return_value.insert.return_value.execute.return_value = mock_create_response
            
            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.post(
                    "/api/v1/membership-requests/",
                    json={
                        "domain_id": "domain123"
                    }
                )
                
                assert response.status_code == 201
                data = response.json()
                assert data["message"] is None

"""Tests for user management endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from src.service.api import app

client = TestClient(app)


class TestUserEndpoints:
    """Test cases for user management endpoints."""

    def test_get_user_profile_success(self):
        """Test successful user profile retrieval."""
        mock_user = {
            "id": "user123",
            "email": "test@example.com",
            "role": "contributor",
            "domain_id": "domain123",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "first_name": "John",
            "last_name": "Doe",
            "avatar_url": "https://example.com/avatar.jpg",
            "bio": "Test user"
        }
        
        with patch('src.app.auth.models.UserModel.get_user_by_id', return_value=mock_user):
            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.get("/api/v1/users/user123/profile")
                
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == "user123"
                assert data["email"] == "test@example.com"
                assert data["role"] == "contributor"
                assert data["profile"]["first_name"] == "John"
                assert data["profile"]["last_name"] == "Doe"

    def test_get_user_profile_not_found(self):
        """Test user profile not found."""
        with patch('src.app.auth.models.UserModel.get_user_by_id', return_value=None):
            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.get("/api/v1/users/user123/profile")
                
                assert response.status_code == 404
                assert "User not found" in response.json()["detail"]

    def test_get_user_profile_access_denied(self):
        """Test access denied when trying to view another user's profile."""
        with patch('src.app.auth.dependencies.get_current_user_id', return_value="user456"):
            response = client.get("/api/v1/users/user123/profile")
            
            assert response.status_code == 403
            assert "Access denied" in response.json()["detail"]

    def test_get_user_domains_success(self):
        """Test successful user domains retrieval."""
        mock_owned_domains = [
            {
                "id": "domain1",
                "name": "Domain 1",
                "description": "Test domain 1",
                "owner_id": "user123"
            }
        ]
        
        mock_memberships = [
            {
                "domain_id": "domain2",
                "role": "member",
                "domains": {
                    "id": "domain2",
                    "name": "Domain 2",
                    "description": "Test domain 2"
                }
            }
        ]
        
        with patch('src.app.clients.supabase.get_supabase_client') as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            
            # Mock owned domains response
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_owned_domains
            
            # Mock memberships response
            mock_memberships_response = Mock()
            mock_memberships_response.data = mock_memberships
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_memberships_response
            
            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.get("/api/v1/users/user123/domains")
                
                assert response.status_code == 200
                data = response.json()
                assert "domains" in data
                assert "total_count" in data
                assert "pagination" in data

    def test_get_user_domains_access_denied(self):
        """Test access denied when trying to view another user's domains."""
        with patch('src.app.auth.dependencies.get_current_user_id', return_value="user456"):
            response = client.get("/api/v1/users/user123/domains")
            
            assert response.status_code == 403
            assert "Access denied" in response.json()["detail"]

    def test_get_user_membership_requests_success(self):
        """Test successful membership requests retrieval."""
        mock_requests = [
            {
                "id": "request1",
                "user_id": "user123",
                "domain_id": "domain1",
                "status": "pending",
                "message": "Please accept me",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "domains": {
                    "name": "Test Domain",
                    "description": "A test domain"
                },
                "users": {
                    "email": "test@example.com",
                    "first_name": "John",
                    "last_name": "Doe"
                }
            }
        ]
        
        with patch('src.app.clients.supabase.get_supabase_client') as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            
            mock_response = Mock()
            mock_response.data = mock_requests
            mock_client.table.return_value.select.return_value.eq.return_value.range.return_value.execute.return_value = mock_response
            
            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.get("/api/v1/users/user123/membership-requests")
                
                assert response.status_code == 200
                data = response.json()
                assert "membership_requests" in data
                assert len(data["membership_requests"]) == 1
                assert data["membership_requests"][0]["id"] == "request1"

    def test_get_user_membership_requests_with_filters(self):
        """Test membership requests with status filter."""
        with patch('src.app.clients.supabase.get_supabase_client') as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            
            mock_response = Mock()
            mock_response.data = []
            mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.range.return_value.execute.return_value = mock_response
            
            with patch('src.app.auth.dependencies.get_current_user_id', return_value="user123"):
                response = client.get("/api/v1/users/user123/membership-requests?status_filter=pending")
                
                assert response.status_code == 200
                data = response.json()
                assert data["filters"]["status"] == "pending"

    def test_get_user_membership_requests_access_denied(self):
        """Test access denied when trying to view another user's membership requests."""
        with patch('src.app.auth.dependencies.get_current_user_id', return_value="user456"):
            response = client.get("/api/v1/users/user123/membership-requests")
            
            assert response.status_code == 403
            assert "Access denied" in response.json()["detail"]

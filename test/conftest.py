"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_document_id() -> str:
    """Sample document ID for testing."""
    return "123e4567-e89b-12d3-a456-426614174000"


@pytest.fixture
def sample_domain_id() -> str:
    """Sample domain ID for testing."""
    return "456e4567-e89b-12d3-a456-426614174001"


@pytest.fixture
def sample_user_id() -> str:
    """Sample user ID for testing."""
    return "789e4567-e89b-12d3-a456-426614174002"

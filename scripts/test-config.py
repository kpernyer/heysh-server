#!/usr/bin/env python3
"""
Test configuration script.
Tests that all configurations work correctly.
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.hostnames import hostname_config
from config.constants import Constants


def test_configuration():
    """Test configuration functionality."""
    print("🧪 Testing configuration...")

    try:
        # Test hostname retrieval
        app_hostname = hostname_config.get_hostname("app")
        api_hostname = hostname_config.get_hostname("api")
        print(f"  ✓ App hostname: {app_hostname}")
        print(f"  ✓ API hostname: {api_hostname}")

        # Test port retrieval
        backend_port = hostname_config.get_port("backend")
        frontend_port = hostname_config.get_port("frontend")
        print(f"  ✓ Backend port: {backend_port}")
        print(f"  ✓ Frontend port: {frontend_port}")

        # Test service URL retrieval
        backend_url = hostname_config.get_service_url("backend")
        frontend_url = hostname_config.get_service_url("frontend")
        print(f"  ✓ Backend URL: {backend_url}")
        print(f"  ✓ Frontend URL: {frontend_url}")

        # Test constants
        print(f"  ✓ API base URL: {Constants.API_BASE_URL}")
        print(f"  ✓ Health check endpoint: {Constants.HEALTH_CHECK_ENDPOINT}")

        print("\n✅ Configuration testing passed")
        return True

    except Exception as e:
        print(f"\n❌ Configuration testing failed: {e}")
        return False


if __name__ == "__main__":
    success = test_configuration()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Configuration validation script.
Validates that all configurations are correct and consistent.
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.hostnames import hostname_config
from config.constants import Constants


def validate_configuration():
    """Validate all configuration settings."""
    print("🔍 Validating configuration...")

    errors = []

    # Validate hostname configuration
    try:
        print("  ✓ Hostname configuration loaded")
        print(f"    Environment: {hostname_config.environment}")
        print(f"    App hostname: {hostname_config.app_hostname}")
        print(f"    API hostname: {hostname_config.api_hostname}")
    except Exception as e:
        errors.append(f"Hostname configuration error: {e}")

    # Validate port allocation
    try:
        ports = hostname_config.ports
        dev_ports = hostname_config.dev_ports

        # Check for port conflicts within each environment
        # Production ports should be unique
        prod_ports = list(ports.values())
        if len(prod_ports) != len(set(prod_ports)):
            conflicts = [p for p in set(prod_ports) if prod_ports.count(p) > 1]
            errors.append(f"Production port conflicts: {conflicts}")

        # Development ports should be unique
        dev_ports_list = list(dev_ports.values())
        if len(dev_ports_list) != len(set(dev_ports_list)):
            conflicts = [p for p in set(dev_ports_list) if dev_ports_list.count(p) > 1]
            errors.append(f"Development port conflicts: {conflicts}")

        # Check for conflicts between production and development (except Caddy ports)
        allowed_shared_ports = {80, 443}  # Caddy ports can be shared
        prod_ports_filtered = [p for p in prod_ports if p not in allowed_shared_ports]
        dev_ports_filtered = [
            p for p in dev_ports_list if p not in allowed_shared_ports
        ]

        cross_conflicts = set(prod_ports_filtered) & set(dev_ports_filtered)
        if cross_conflicts:
            errors.append(f"Cross-environment port conflicts: {list(cross_conflicts)}")

        print("  ✓ Port allocation validated")
        print(f"    Production ports: {ports}")
        print(f"    Development ports: {dev_ports}")
    except Exception as e:
        errors.append(f"Port allocation error: {e}")

    # Validate constants
    try:
        print("  ✓ Constants loaded")
        print(f"    API base URL: {Constants.API_BASE_URL}")
        print(f"    Health check endpoint: {Constants.HEALTH_CHECK_ENDPOINT}")
    except Exception as e:
        errors.append(f"Constants error: {e}")

    if errors:
        print("\n❌ Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("\n✅ Configuration validation passed")
        return True


if __name__ == "__main__":
    success = validate_configuration()
    sys.exit(0 if success else 1)

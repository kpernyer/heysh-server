#!/usr/bin/env python3
"""Get configuration values for justfile."""

import sys
import os

# Add config directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config'))

from hostnames import hostname_config

def get_port(service: str) -> int:
    """Get port for service."""
    return hostname_config.get_port(service)

def get_hostname(service: str) -> str:
    """Get hostname for service."""
    return hostname_config.get_hostname(service)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python get_config.py <service> <type>")
        print("  service: backend, frontend, temporal, temporal_ui, etc.")
        print("  type: port, hostname")
        sys.exit(1)
    
    service = sys.argv[1]
    config_type = sys.argv[2]
    
    try:
        if config_type == "port":
            print(hostname_config.get_port(service))
        elif config_type == "hostname":
            print(hostname_config.get_hostname(service))
        else:
            print(f"Unknown type: {config_type}")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

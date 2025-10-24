#!/usr/bin/env python3
"""
Service discovery script.
Discovers and reports on all services in the environment.
"""

import sys
import os
import requests

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.hostnames import hostname_config


def discover_services():
    """Discover and report on all services."""
    print("🔍 Discovering services...")

    services = {
        "frontend": {
            "hostname": hostname_config.get_hostname("app"),
            "port": hostname_config.get_port("frontend"),
            "url": f"https://{hostname_config.get_hostname('app')}",
        },
        "backend": {
            "hostname": hostname_config.get_hostname("api"),
            "port": hostname_config.get_port("backend"),
            "url": f"https://{hostname_config.get_hostname('api')}",
        },
        "temporal": {
            "hostname": hostname_config.get_hostname("temporal"),
            "port": hostname_config.get_port("temporal_ui"),
            "url": f"https://{hostname_config.get_hostname('temporal')}",
        },
        "grafana": {
            "hostname": hostname_config.get_hostname("grafana"),
            "port": hostname_config.get_port("grafana"),
            "url": f"https://{hostname_config.get_hostname('grafana')}",
        },
        "prometheus": {
            "hostname": hostname_config.get_hostname("prometheus"),
            "port": hostname_config.get_port("prometheus"),
            "url": f"https://{hostname_config.get_hostname('prometheus')}",
        },
    }

    print("📋 Service Discovery Results:")
    print("=" * 50)

    for service_name, service_info in services.items():
        print(f"\n🔧 {service_name.upper()}")
        print(f"  Hostname: {service_info['hostname']}")
        print(f"  Port: {service_info['port']}")
        print(f"  URL: {service_info['url']}")

        # Try to check health
        try:
            response = requests.get(f"{service_info['url']}/health", timeout=5)
            if response.status_code == 200:
                print("  Status: ✅ Healthy")
            else:
                print(
                    f"  Status: ⚠️  Responding but not healthy (HTTP {response.status_code})"
                )
        except requests.exceptions.RequestException:
            print("  Status: ❌ Not responding")

    print("\n" + "=" * 50)
    print("🔍 Service discovery completed")


if __name__ == "__main__":
    discover_services()

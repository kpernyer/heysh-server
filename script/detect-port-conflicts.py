#!/usr/bin/env python3
"""
Port conflict detection script.
Detects and reports on port conflicts in the system.
"""

import sys
import os
import socket

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.hostnames import hostname_config


def check_port(host, port):
    """Check if a port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result == 0
    except:
        return False


def detect_port_conflicts():
    """Detect port conflicts."""
    print("🔍 Detecting port conflicts...")

    # Get all ports from configuration
    ports = hostname_config.ports
    dev_ports = hostname_config.dev_ports

    all_ports = {}
    for service, port in ports.items():
        all_ports[f"{service}_prod"] = port
    for service, port in dev_ports.items():
        all_ports[f"{service}_dev"] = port

    print("📋 Port Allocation:")
    print("=" * 50)

    conflicts = []
    for service, port in all_ports.items():
        status = "✅ Available" if not check_port("localhost", port) else "❌ In Use"
        print(f"  {service:20} Port {port:5} {status}")

        if check_port("localhost", port):
            conflicts.append((service, port))

    if conflicts:
        print("\n⚠️  Port conflicts detected:")
        for service, port in conflicts:
            print(f"  - {service} (port {port})")
    else:
        print("\n✅ No port conflicts detected")

    print("\n" + "=" * 50)
    print("🔍 Port conflict detection completed")


if __name__ == "__main__":
    detect_port_conflicts()

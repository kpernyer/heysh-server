#!/bin/bash

# Phase 2 Implementation Script
# This script implements port management and Docker updates

set -e

echo "🚀 Starting Phase 2 Implementation: Port Management & Docker Updates"
echo ""

# Install required dependencies
echo "📦 Installing required dependencies..."
uv add pyyaml > /dev/null 2>&1 || echo "PyYAML already installed"

# Generate configurations from centralized config
echo "🔧 Generating configurations from centralized config..."

# Generate Docker Compose configurations
echo "🐳 Generating Docker Compose configurations..."
python3 scripts/generate-docker-config.py

# Generate Kubernetes configurations
echo "☸️  Generating Kubernetes configurations..."
python3 scripts/generate-k8s-config.py

# Create monitoring configuration
echo "📊 Creating monitoring configuration..."
mkdir -p monitoring

cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'frontend'
    static_configs:
      - targets: ['frontend:3000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'temporal'
    static_configs:
      - targets: ['temporal:7233']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    metrics_path: '/metrics'
    scrape_interval: 30s
EOF

echo "✅ Monitoring configuration created"

# Create health check scripts
echo "🏥 Creating health check scripts..."
mkdir -p scripts/health

cat > scripts/health/check-services.sh << 'EOF'
#!/bin/bash

# Health check script for all services
echo "🏥 Checking service health..."

# Check Caddy
echo "Checking Caddy..."
if curl -s -f http://localhost:80 > /dev/null; then
    echo "  ✅ Caddy is healthy"
else
    echo "  ❌ Caddy is not responding"
fi

# Check backend
echo "Checking Backend..."
if curl -s -f http://localhost:8000/health > /dev/null; then
    echo "  ✅ Backend is healthy"
else
    echo "  ❌ Backend is not responding"
fi

# Check frontend
echo "Checking Frontend..."
if curl -s -f http://localhost:3000 > /dev/null; then
    echo "  ✅ Frontend is healthy"
else
    echo "  ❌ Frontend is not responding"
fi

# Check Temporal
echo "Checking Temporal..."
if curl -s -f http://localhost:8080 > /dev/null; then
    echo "  ✅ Temporal UI is healthy"
else
    echo "  ❌ Temporal UI is not responding"
fi

# Check PostgreSQL
echo "Checking PostgreSQL..."
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "  ✅ PostgreSQL is healthy"
else
    echo "  ❌ PostgreSQL is not responding"
fi

# Check Redis
echo "Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo "  ✅ Redis is healthy"
else
    echo "  ❌ Redis is not responding"
fi

echo "🏥 Health check completed"
EOF

chmod +x scripts/health/check-services.sh

# Create service discovery script
echo "🔍 Creating service discovery script..."

cat > scripts/discover-services.py << 'EOF'
#!/usr/bin/env python3
"""
Service discovery script.
Discovers and reports on all services in the environment.
"""

import sys
import os
import requests
import json
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.hostnames import hostname_config
from config.constants import Constants

def discover_services():
    """Discover and report on all services."""
    print("🔍 Discovering services...")

    services = {
        "frontend": {
            "hostname": hostname_config.get_hostname("app"),
            "port": hostname_config.get_port("frontend"),
            "url": f"https://{hostname_config.get_hostname('app')}"
        },
        "backend": {
            "hostname": hostname_config.get_hostname("api"),
            "port": hostname_config.get_port("backend"),
            "url": f"https://{hostname_config.get_hostname('api')}"
        },
        "temporal": {
            "hostname": hostname_config.get_hostname("temporal"),
            "port": hostname_config.get_port("temporal_ui"),
            "url": f"https://{hostname_config.get_hostname('temporal')}"
        },
        "grafana": {
            "hostname": hostname_config.get_hostname("grafana"),
            "port": hostname_config.get_port("grafana"),
            "url": f"https://{hostname_config.get_hostname('grafana')}"
        },
        "prometheus": {
            "hostname": hostname_config.get_hostname("prometheus"),
            "port": hostname_config.get_port("prometheus"),
            "url": f"https://{hostname_config.get_hostname('prometheus')}"
        }
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
                print(f"  Status: ✅ Healthy")
            else:
                print(f"  Status: ⚠️  Responding but not healthy (HTTP {response.status_code})")
        except requests.exceptions.RequestException:
            print(f"  Status: ❌ Not responding")

    print("\n" + "=" * 50)
    print("🔍 Service discovery completed")

if __name__ == "__main__":
    discover_services()
EOF

chmod +x scripts/discover-services.py

# Create port conflict detection script
echo "🔍 Creating port conflict detection script..."

cat > scripts/detect-port-conflicts.py << 'EOF'
#!/usr/bin/env python3
"""
Port conflict detection script.
Detects and reports on port conflicts in the system.
"""

import sys
import os
import socket
from pathlib import Path

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
        print(f"\n⚠️  Port conflicts detected:")
        for service, port in conflicts:
            print(f"  - {service} (port {port})")
    else:
        print(f"\n✅ No port conflicts detected")

    print("\n" + "=" * 50)
    print("🔍 Port conflict detection completed")

if __name__ == "__main__":
    detect_port_conflicts()
EOF

chmod +x scripts/detect-port-conflicts.py

# Create Docker network management script
echo "🐳 Creating Docker network management script..."

cat > scripts/docker-network.sh << 'EOF'
#!/bin/bash

# Docker network management script
echo "🐳 Managing Docker networks..."

# Create hey-network if it doesn't exist
if ! docker network ls | grep -q hey-network; then
    echo "Creating hey-network..."
    docker network create hey-network
    echo "✅ hey-network created"
else
    echo "✅ hey-network already exists"
fi

# List all networks
echo "📋 Available Docker networks:"
docker network ls

# Show network details
echo "🔍 hey-network details:"
docker network inspect hey-network

echo "🐳 Docker network management completed"
EOF

chmod +x scripts/docker-network.sh

# Test all configurations
echo "🧪 Testing configurations..."

# Test port conflict detection
echo "🔍 Testing port conflict detection..."
python3 scripts/detect-port-conflicts.py

# Test service discovery
echo "🔍 Testing service discovery..."
python3 scripts/discover-services.py

# Test Docker network
echo "🐳 Testing Docker network..."
./scripts/docker-network.sh

# Test health checks
echo "🏥 Testing health checks..."
./scripts/health/check-services.sh

echo ""
echo "🎉 Phase 2 Implementation Complete!"
echo ""
echo "✅ Port management implemented"
echo "✅ Docker Compose configurations updated"
echo "✅ Kubernetes configurations updated"
echo "✅ Service discovery implemented"
echo "✅ Health checks implemented"
echo "✅ Port conflict detection implemented"
echo "✅ Docker network management implemented"
echo ""
echo "Generated configurations:"
echo "  - docker/generated/docker-compose.dev.yml"
echo "  - k8s/generated/ingress.yaml"
echo "  - k8s/generated/services.yaml"
echo "  - monitoring/prometheus.yml"
echo ""
echo "Available scripts:"
echo "  - scripts/detect-port-conflicts.py"
echo "  - scripts/discover-services.py"
echo "  - scripts/docker-network.sh"
echo "  - scripts/health/check-services.sh"
echo ""
echo "Next steps:"
echo "1. Review generated configurations"
echo "2. Test Docker Compose: docker-compose -f docker/generated/docker-compose.dev.yml up -d"
echo "3. Test Kubernetes: kubectl apply -f k8s/generated/"
echo "4. Monitor services: ./scripts/health/check-services.sh"
echo ""
echo "For detailed implementation guide, see: doc/PHASE_2_IMPLEMENTATION.md"

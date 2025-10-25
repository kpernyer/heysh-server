"""Test connectivity to all services."""

import requests
import socket
import time
from typing import Dict, Any


def test_port_connectivity(host: str, port: int, service_name: str) -> bool:
    """Test if a port is open and accepting connections."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def test_http_endpoint(url: str, service_name: str) -> Dict[str, Any]:
    """Test HTTP endpoint connectivity."""
    try:
        response = requests.get(url, timeout=10)
        return {
            "service": service_name,
            "url": url,
            "status": "✅ Connected",
            "status_code": response.status_code,
            "response_time": response.elapsed.total_seconds()
        }
    except requests.exceptions.RequestException as e:
        return {
            "service": service_name,
            "url": url,
            "status": "❌ Failed",
            "error": str(e)
        }


def main():
    """Run comprehensive connectivity tests."""
    print("🧪 Testing Service Connectivity")
    print("=" * 50)
    
    # Test results
    results = []
    
    # Test API Server
    api_result = test_http_endpoint("http://localhost:8002/health", "API Server")
    results.append(api_result)
    
    # Test Neo4j
    neo4j_result = test_http_endpoint("http://localhost:7474", "Neo4j")
    results.append(neo4j_result)
    
    # Test Weaviate
    weaviate_result = test_http_endpoint("http://localhost:8082/v1/meta", "Weaviate")
    results.append(weaviate_result)
    
    # Test Temporal UI
    temporal_ui_result = test_http_endpoint("http://localhost:8090", "Temporal UI")
    results.append(temporal_ui_result)
    
    # Test Caddy (just check if port is open)
    caddy_port_open = test_port_connectivity("localhost", 80, "Caddy")
    results.append({
        "service": "Caddy",
        "url": "localhost:80",
        "status": "✅ Connected" if caddy_port_open else "❌ Failed",
        "port_open": caddy_port_open
    })
    
    # Test port connectivity for services that don't have HTTP endpoints
    port_tests = [
        ("Temporal", "localhost", 7233),
        ("PostgreSQL", "localhost", 5432),
        ("Redis", "localhost", 6379),
        ("MinIO", "localhost", 9000),
    ]
    
    for service_name, host, port in port_tests:
        is_open = test_port_connectivity(host, port, service_name)
        results.append({
            "service": service_name,
            "url": f"{host}:{port}",
            "status": "✅ Connected" if is_open else "❌ Failed",
            "port_open": is_open
        })
    
    # Print results
    print("\n📊 Service Status:")
    print("-" * 50)
    
    for result in results:
        status_icon = "✅" if "✅" in result["status"] else "❌"
        print(f"{status_icon} {result['service']}: {result['url']}")
        
        if "status_code" in result:
            print(f"   Status: {result['status_code']}")
        if "response_time" in result:
            print(f"   Response Time: {result['response_time']:.3f}s")
        if "error" in result:
            print(f"   Error: {result['error']}")
        if "port_open" in result:
            print(f"   Port Open: {result['port_open']}")
    
    # Summary
    successful = sum(1 for r in results if "✅" in r["status"])
    total = len(results)
    
    print(f"\n📈 Summary: {successful}/{total} services running")
    
    if successful == total:
        print("🎉 All services are running successfully!")
        return True
    else:
        print("⚠️  Some services are not responding")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

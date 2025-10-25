#!/usr/bin/env python3
"""
Generate Kubernetes configurations from centralized configuration.
This script uses the centralized hostname and port configuration to generate
Kubernetes manifests with the correct values.
"""

import sys
import os
import yaml
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.hostnames import hostname_config


def generate_k8s_config():
    """Generate Kubernetes configuration from centralized config."""
    print("🔧 Generating Kubernetes configuration from centralized config...")

    # Get configuration values
    app_hostname = hostname_config.get_hostname("app")
    api_hostname = hostname_config.get_hostname("api")
    temporal_hostname = hostname_config.get_hostname("temporal")
    grafana_hostname = hostname_config.get_hostname("grafana")
    prometheus_hostname = hostname_config.get_hostname("prometheus")

    # Get port values
    backend_port = hostname_config.get_port("backend")
    frontend_port = hostname_config.get_port("frontend")
    temporal_port = hostname_config.get_port("temporal")
    temporal_ui_port = hostname_config.get_port("temporal_ui")
    grafana_port = hostname_config.get_port("grafana")
    prometheus_port = hostname_config.get_port("prometheus")

    # Generate ingress configuration
    ingress_config = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {
            "name": "hey-sh-ingress",
            "namespace": "hey-sh",
            "annotations": {
                "kubernetes.io/ingress.class": "caddy",
                "caddy.ingress.kubernetes.io/rewrite": "/",
                "caddy.ingress.kubernetes.io/tls": "true",
                "caddy.ingress.kubernetes.io/rate-limit": "100",
                "caddy.ingress.kubernetes.io/cors": "true",
            },
        },
        "spec": {
            "tls": [
                {
                    "hosts": [
                        app_hostname,
                        api_hostname,
                        temporal_hostname,
                        grafana_hostname,
                        prometheus_hostname,
                    ],
                    "secretName": "hey-sh-tls",
                }
            ],
            "rules": [
                {
                    "host": app_hostname,
                    "http": {
                        "paths": [
                            {
                                "path": "/",
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": "frontend-service",
                                        "port": {"number": frontend_port},
                                    }
                                },
                            }
                        ]
                    },
                },
                {
                    "host": api_hostname,
                    "http": {
                        "paths": [
                            {
                                "path": "/",
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": "backend-service",
                                        "port": {"number": backend_port},
                                    }
                                },
                            }
                        ]
                    },
                },
                {
                    "host": temporal_hostname,
                    "http": {
                        "paths": [
                            {
                                "path": "/",
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": "temporal-ui-service",
                                        "port": {"number": temporal_ui_port},
                                    }
                                },
                            }
                        ]
                    },
                },
                {
                    "host": grafana_hostname,
                    "http": {
                        "paths": [
                            {
                                "path": "/",
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": "grafana-service",
                                        "port": {"number": grafana_port},
                                    }
                                },
                            }
                        ]
                    },
                },
                {
                    "host": prometheus_hostname,
                    "http": {
                        "paths": [
                            {
                                "path": "/",
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": "prometheus-service",
                                        "port": {"number": prometheus_port},
                                    }
                                },
                            }
                        ]
                    },
                },
            ],
        },
    }

    # Generate services configuration
    services_config = [
        {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "frontend-service",
                "namespace": "hey-sh",
                "labels": {"app": "frontend"},
            },
            "spec": {
                "type": "ClusterIP",
                "ports": [
                    {
                        "port": frontend_port,
                        "targetPort": frontend_port,
                        "protocol": "TCP",
                        "name": "http",
                    }
                ],
                "selector": {"app": "frontend"},
            },
        },
        {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "backend-service",
                "namespace": "hey-sh",
                "labels": {"app": "backend"},
            },
            "spec": {
                "type": "ClusterIP",
                "ports": [
                    {
                        "port": backend_port,
                        "targetPort": backend_port,
                        "protocol": "TCP",
                        "name": "http",
                    }
                ],
                "selector": {"app": "backend"},
            },
        },
        {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "temporal-ui-service",
                "namespace": "hey-sh",
                "labels": {"app": "temporal-ui"},
            },
            "spec": {
                "type": "ClusterIP",
                "ports": [
                    {
                        "port": temporal_ui_port,
                        "targetPort": temporal_ui_port,
                        "protocol": "TCP",
                        "name": "http",
                    }
                ],
                "selector": {"app": "temporal-ui"},
            },
        },
        {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "grafana-service",
                "namespace": "hey-sh",
                "labels": {"app": "grafana"},
            },
            "spec": {
                "type": "ClusterIP",
                "ports": [
                    {
                        "port": grafana_port,
                        "targetPort": grafana_port,
                        "protocol": "TCP",
                        "name": "http",
                    }
                ],
                "selector": {"app": "grafana"},
            },
        },
        {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "prometheus-service",
                "namespace": "hey-sh",
                "labels": {"app": "prometheus"},
            },
            "spec": {
                "type": "ClusterIP",
                "ports": [
                    {
                        "port": prometheus_port,
                        "targetPort": prometheus_port,
                        "protocol": "TCP",
                        "name": "http",
                    }
                ],
                "selector": {"app": "prometheus"},
            },
        },
    ]

    # Write configurations to files
    k8s_dir = Path("k8s/generated")
    k8s_dir.mkdir(parents=True, exist_ok=True)

    # Write ingress configuration
    with open(k8s_dir / "ingress.yaml", "w") as f:
        yaml.dump(ingress_config, f, default_flow_style=False, sort_keys=False)

    # Write services configuration
    with open(k8s_dir / "services.yaml", "w") as f:
        for service in services_config:
            yaml.dump(service, f, default_flow_style=False, sort_keys=False)
            f.write("---\n")

    print("✅ Kubernetes configuration generated")
    print(f"  Ingress: {k8s_dir / 'ingress.yaml'}")
    print(f"  Services: {k8s_dir / 'services.yaml'}")
    print(f"  Hostnames: {app_hostname}, {api_hostname}, {temporal_hostname}")
    print(
        f"  Ports: Frontend={frontend_port}, Backend={backend_port}, Temporal={temporal_ui_port}"
    )


if __name__ == "__main__":
    generate_k8s_config()

"""
Example of how to use the centralized configuration.
This shows the ONLY way to get URLs and hostnames in the codebase.
"""

from src.config import (
    # Environment info
    ENVIRONMENT, 
    config,
    
    # Pre-built URLs (use these constants everywhere)
    API_URL,
    FRONTEND_URL,
    TEMPORAL_URL,
    NEO4J_URL,
    WEAVIATE_URL,
    
    # Local URLs for direct access
    API_LOCAL_URL,
    NEO4J_LOCAL_URL,
)

def example_usage():
    """Example of how to use the configuration."""
    
    # ✅ CORRECT: Use the pre-built constants
    print(f"API URL: {API_URL}")
    print(f"Frontend URL: {FRONTEND_URL}")
    print(f"Neo4j URL: {NEO4J_URL}")
    
    # ✅ CORRECT: Use the config object for dynamic URLs
    custom_url = config.get_url("api", "/health")
    print(f"Health check URL: {custom_url}")
    
    # ✅ CORRECT: Get local URLs for direct access
    print(f"API Local: {API_LOCAL_URL}")
    print(f"Neo4j Local: {NEO4J_LOCAL_URL}")
    
    # ✅ CORRECT: Check environment
    if config.is_development:
        print("Running in development mode")
    elif config.is_production:
        print("Running in production mode")
    
    # ❌ WRONG: Don't hardcode URLs
    # bad_url = "http://localhost:8002"  # DON'T DO THIS
    
    # ❌ WRONG: Don't construct URLs manually
    # bad_url = f"http://api.hey.local"  # DON'T DO THIS

if __name__ == "__main__":
    example_usage()

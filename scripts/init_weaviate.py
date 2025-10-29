#!/usr/bin/env python3
"""Initialize Weaviate with schema and test data."""

import sys
import time
from urllib.parse import urlparse

import weaviate
from weaviate.classes.config import Configure, DataType, Property


def init_weaviate(url: str) -> bool:
    """Initialize Weaviate with document schema.

    Args:
        url: Weaviate URL (e.g., http://weaviate.hey.local)

    Returns:
        True if successful, False otherwise
    """
    print(f"🔌 Connecting to Weaviate at {url}...")

    # Parse URL
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 8080

    try:
        # Connect to Weaviate (skip gRPC init checks - we're using HTTP only)
        client = weaviate.connect_to_local(host=host, port=port, skip_init_checks=True)

        print(f"✅ Connected to Weaviate v{client.get_meta()['version']}")

        # Check if Document collection exists
        collection_name = "Document"

        if client.collections.exists(collection_name):
            print(f"📦 Collection '{collection_name}' already exists")
            collection = client.collections.get(collection_name)
        else:
            print(f"📦 Creating collection '{collection_name}'...")

            # Create Document collection with schema
            collection = client.collections.create(
                name=collection_name,
                description="Document chunks for semantic search",
                vectorizer_config=Configure.Vectorizer.none(),  # We'll provide embeddings
                properties=[
                    Property(
                        name="document_id",
                        data_type=DataType.TEXT,
                        description="UUID of the document",
                    ),
                    Property(
                        name="topic_id",
                        data_type=DataType.TEXT,
                        description="UUID of the topic (formerly domain_id)",
                    ),
                    Property(
                        name="text",
                        data_type=DataType.TEXT,
                        description="Document chunk text content",
                    ),
                    Property(
                        name="chunk_index",
                        data_type=DataType.INT,
                        description="Index of this chunk in the document",
                    ),
                    Property(
                        name="metadata",
                        data_type=DataType.TEXT,
                        description="Additional metadata as JSON string",
                    ),
                ],
            )
            print(f"✅ Created collection '{collection_name}'")

        # Add a test document to verify it's working
        print("🧪 Adding test document...")

        test_doc = {
            "document_id": "test-doc-001",
            "topic_id": "test-topic-001",
            "text": "This is a test document to verify Weaviate is working correctly with semantic search.",
            "chunk_index": 0,
            "metadata": '{"test": true}',
        }

        # Insert test document (with dummy embedding)
        test_vector = [0.1] * 1536  # OpenAI embedding dimension

        uuid = collection.data.insert(
            properties=test_doc,
            vector=test_vector,
        )

        print(f"✅ Added test document with UUID: {uuid}")

        # Verify by reading it back
        obj = collection.query.fetch_object_by_id(uuid)
        if obj:
            print(f"✅ Verified: Can read test document")
            print(f"   Text: {obj.properties.get('text')[:50]}...")

        # Get collection stats
        agg = collection.aggregate.over_all(total_count=True)
        count = agg.total_count
        print(f"📊 Collection stats: {count} objects")

        client.close()
        print("✅ Weaviate initialization complete!")
        return True

    except Exception as e:
        print(f"❌ Error initializing Weaviate: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    # Get URL from environment or use default
    # Use localhost:8082 for direct connection (not via Caddy)
    import os

    url = os.getenv("WEAVIATE_URL", "http://localhost:8082")

    # Wait a bit for Weaviate to be ready
    print("⏳ Waiting for Weaviate to be ready...")
    time.sleep(2)

    success = init_weaviate(url)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

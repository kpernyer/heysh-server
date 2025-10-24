#!/usr/bin/env python3
"""Setup Weaviate schema for Domain objects."""

import os
import sys

import weaviate
import weaviate.classes as wvc
from dotenv import load_dotenv

load_dotenv()


def setup_schema():
    """Create Domain class schema in Weaviate."""
    # Weaviate v4 client - skip gRPC checks for faster initialization
    client = weaviate.connect_to_local(
        host="localhost",
        port=8082,
        headers={
            "X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY", ""),
        },
        skip_init_checks=True,
    )

    try:
        # Check if Domain collection already exists
        if client.collections.exists("Domain"):
            print("✅ Domain collection already exists in Weaviate")
            return

        # Create Domain collection with OpenAI vectorizer
        client.collections.create(
            name="Domain",
            description="A collaborative domain/topic on the hey.sh platform",
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(
                model="text-embedding-3-small",
            ),
            properties=[
                wvc.config.Property(
                    name="domain_id",
                    data_type=wvc.config.DataType.TEXT,
                    description="Unique domain identifier",
                ),
                wvc.config.Property(
                    name="name",
                    data_type=wvc.config.DataType.TEXT,
                    description="Domain name",
                ),
                wvc.config.Property(
                    name="description",
                    data_type=wvc.config.DataType.TEXT,
                    description="Domain description",
                ),
                wvc.config.Property(
                    name="created_by",
                    data_type=wvc.config.DataType.TEXT,
                    description="User ID who created the domain",
                ),
                wvc.config.Property(
                    name="text",
                    data_type=wvc.config.DataType.TEXT,
                    description="Searchable text (name + description)",
                ),
                wvc.config.Property(
                    name="type",
                    data_type=wvc.config.DataType.TEXT,
                    description="Object type (domain)",
                ),
            ],
        )

        print("✅ Created Domain collection schema in Weaviate")
        print("   - Vectorizer: text2vec-openai")
        print("   - Model: text-embedding-3-small")

    except Exception as e:
        print(f"❌ Failed to create schema: {e}")
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    print("🔧 Setting up Weaviate schema...")
    print("")
    setup_schema()
    print("")
    print("✅ Weaviate schema setup complete!")

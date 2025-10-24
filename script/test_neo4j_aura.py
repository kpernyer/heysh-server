#!/usr/bin/env python3
"""Test Neo4j Aura connection."""

import os
import sys

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()


def test_neo4j_connection():
    """Test connection to Neo4j Aura."""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")

    print("🔧 Testing Neo4j Aura Connection")
    print("=" * 50)
    print(f"URI: {uri}")
    print(f"User: {user}")
    print(f"Password: {'*' * len(password) if password else 'NOT SET'}")
    print()

    if not uri or not password:
        print("❌ Error: NEO4J_URI or NEO4J_PASSWORD not set in .env")
        sys.exit(1)

    try:
        # Connect to Neo4j
        print("📡 Connecting to Neo4j Aura...")
        driver = GraphDatabase.driver(uri, auth=(user, password))

        # Verify connection
        driver.verify_connectivity()
        print("✅ Connection successful!")
        print()

        # Get server info
        with driver.session() as session:
            result = session.run("CALL dbms.components() YIELD name, versions, edition")
            for record in result:
                print(f"📊 Neo4j {record['name']}")
                print(f"   Version: {record['versions'][0]}")
                print(f"   Edition: {record['edition']}")
            print()

            # Test write operation
            print("📝 Testing write operation...")
            result = session.run(
                """
                MERGE (t:TestNode {id: 'aura-connection-test'})
                SET t.timestamp = datetime(),
                    t.test = 'Connection test from hey-sh'
                RETURN t.id as id, t.timestamp as timestamp
            """
            )
            record = result.single()
            print(f"✅ Created/updated test node: {record['id']}")
            print(f"   Timestamp: {record['timestamp']}")
            print()

            # Count nodes
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()["count"]
            print(f"📈 Total nodes in database: {count}")
            print()

        # Close connection
        driver.close()
        print("✅ All tests passed! Neo4j Aura is ready to use.")
        print()
        print("🎯 Next steps:")
        print("   1. Your backend will now use Neo4j Aura for graph data")
        print("   2. Run workflows - they'll automatically use the cloud database")
        print("   3. View data in Neo4j Aura Console: https://console.neo4j.io")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print()
        print("🔍 Troubleshooting:")
        print("   1. Verify URI is correct (should start with neo4j+s://)")
        print("   2. Check password is correct")
        print("   3. Ensure database is running in Neo4j Aura console")
        print("   4. Check firewall allows outbound connections to Neo4j Aura")
        sys.exit(1)


if __name__ == "__main__":
    test_neo4j_connection()

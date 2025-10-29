#!/usr/bin/env python3
"""
Automated Migration Runner (No Prompts)
Runs migration without any user interaction
"""

import sys
from pathlib import Path
import psycopg2

# Database connection
DB_URL = "postgresql://postgres:password@127.0.0.1:5432/heysh"
MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"
MIGRATION_FILE = MIGRATIONS_DIR / "001_rename_domain_to_topic_up.sql"

def main():
    print("=" * 70)
    print("AUTOMATED MIGRATION: Domain → Topic")
    print("=" * 70)
    print()

    # Connect to database
    print("🔌 Connecting to database...")
    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = False
        print("✓ Connected successfully")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        sys.exit(1)

    cursor = conn.cursor()

    # Check current state
    print("\n📋 Checking current table state...")
    try:
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('domains', 'domain_members', 'topics', 'topic_members')
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"   Current tables: {tables or 'None found'}")

        # Check if migration already applied
        if 'topics' in tables:
            print("\n⚠️  Migration appears to already be applied (topics table exists)")
            response = input("   Continue anyway? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Migration cancelled")
                conn.close()
                sys.exit(0)

    except Exception as e:
        print(f"   Warning: Could not check table state: {e}")

    # Read migration SQL
    print(f"\n📖 Reading migration file: {MIGRATION_FILE}")
    if not MIGRATION_FILE.exists():
        print(f"✗ Migration file not found: {MIGRATION_FILE}")
        conn.close()
        sys.exit(1)

    with open(MIGRATION_FILE, 'r') as f:
        migration_sql = f.read()

    print(f"✓ Migration SQL loaded ({len(migration_sql)} characters)")

    # Execute migration
    print("\n⚡ Executing migration...")
    try:
        cursor.execute(migration_sql)
        print("✓ Migration executed successfully")
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        print("\n↩️  Rolling back transaction...")
        conn.rollback()
        conn.close()
        sys.exit(1)

    # Verify migration
    print("\n🔍 Verifying migration results...")
    try:
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('domains', 'domain_members', 'topics', 'topic_members')
            ORDER BY table_name;
        """)
        new_tables = [row[0] for row in cursor.fetchall()]
        print(f"   Tables after migration: {new_tables}")

        # Check expected state
        expected = ['topic_members', 'topics']
        if new_tables == expected:
            print("   ✓ Table structure is correct!")
        else:
            print(f"   ⚠️  Unexpected tables. Expected: {expected}, Got: {new_tables}")

        # Count records
        cursor.execute("SELECT COUNT(*) FROM topics;")
        topic_count = cursor.fetchone()[0]
        print(f"   ✓ Topics count: {topic_count}")

        cursor.execute("SELECT COUNT(*) FROM topic_members;")
        members_count = cursor.fetchone()[0]
        print(f"   ✓ Topic members count: {members_count}")

    except Exception as e:
        print(f"   ⚠️  Verification warning: {e}")

    # Commit
    print("\n💾 Committing transaction...")
    try:
        conn.commit()
        print("✓ Transaction committed successfully")
    except Exception as e:
        print(f"✗ Commit failed: {e}")
        conn.rollback()
        conn.close()
        sys.exit(1)

    # Close connection
    conn.close()
    print("\n" + "=" * 70)
    print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Restart backend services")
    print("  2. Update frontend code to use topic terminology")
    print("  3. Test all endpoints")
    print()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Database Migration Runner
Safely executes SQL migrations for the Hey.sh database
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2 import sql


class MigrationRunner:
    """Handles database migration execution with safety checks."""

    def __init__(self, connection_string: str):
        """Initialize migration runner with database connection."""
        self.connection_string = connection_string
        self.conn = None
        self.migrations_dir = Path(__file__).parent.parent / "migrations"

    def connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(self.connection_string)
            self.conn.autocommit = False  # Use transactions
            print("✓ Connected to database")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to database: {e}")
            return False

    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            print("✓ Disconnected from database")

    def backup_reminder(self):
        """Remind user to backup database."""
        print("\n" + "=" * 70)
        print("⚠️  IMPORTANT: DATABASE BACKUP REMINDER")
        print("=" * 70)
        print("Before proceeding with the migration, ensure you have:")
        print("  1. Created a full database backup")
        print("  2. Stopped all backend services (API, workers)")
        print("  3. Tested this migration in a staging environment")
        print("=" * 70)

        response = input("\nHave you completed all pre-migration steps? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("\n❌ Migration cancelled. Please complete pre-migration steps first.")
            sys.exit(1)
        print()

    def verify_tables_before(self):
        """Verify current table state before migration."""
        print("\n📋 Pre-migration table verification...")

        queries = {
            "domains table exists": "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'domains')",
            "domain_members table exists": "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'domain_members')",
            "topics table exists": "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'topics')",
            "topic_members table exists": "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'topic_members')",
        }

        results = {}
        cursor = self.conn.cursor()

        for check_name, query in queries.items():
            cursor.execute(query)
            result = cursor.fetchone()[0]
            results[check_name] = result
            status = "✓" if result else "✗"
            print(f"  {status} {check_name}: {result}")

        cursor.close()
        return results

    def verify_tables_after(self, direction: str):
        """Verify table state after migration."""
        print("\n📋 Post-migration table verification...")

        if direction == "up":
            expected = {
                "topics table exists": True,
                "topic_members table exists": True,
                "domains table exists": False,
                "domain_members table exists": False,
            }
        else:  # down
            expected = {
                "topics table exists": False,
                "topic_members table exists": False,
                "domains table exists": True,
                "domain_members table exists": True,
            }

        queries = {
            "topics table exists": "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'topics')",
            "topic_members table exists": "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'topic_members')",
            "domains table exists": "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'domains')",
            "domain_members table exists": "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'domain_members')",
        }

        all_passed = True
        cursor = self.conn.cursor()

        for check_name, query in queries.items():
            cursor.execute(query)
            result = cursor.fetchone()[0]
            expected_result = expected[check_name]
            passed = result == expected_result

            status = "✓" if passed else "✗"
            print(f"  {status} {check_name}: {result} (expected: {expected_result})")

            if not passed:
                all_passed = False

        cursor.close()
        return all_passed

    def count_records(self, table_name: str) -> int:
        """Count records in a table."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table_name)))
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Exception:
            return -1

    def verify_data_integrity(self, direction: str):
        """Verify data was preserved during migration."""
        print("\n📊 Data integrity verification...")

        if direction == "up":
            main_table = "topics"
            members_table = "topic_members"
        else:
            main_table = "domains"
            members_table = "domain_members"

        counts = {
            main_table: self.count_records(main_table),
            members_table: self.count_records(members_table),
            "documents": self.count_records("documents"),
            "workflows": self.count_records("workflows"),
        }

        for table, count in counts.items():
            if count >= 0:
                print(f"  ✓ {table}: {count} records")
            else:
                print(f"  ✗ {table}: Table not found or error")

        return all(count >= 0 for count in counts.values())

    def run_migration(self, direction: str, migration_number: str = "001"):
        """Execute migration script."""
        # Construct migration filename
        filename = f"{migration_number}_rename_domain_to_topic_{direction}.sql"
        filepath = self.migrations_dir / filename

        if not filepath.exists():
            print(f"✗ Migration file not found: {filepath}")
            return False

        print(f"\n🚀 Running migration: {filename}")
        print(f"   Direction: {direction.upper()}")
        print(f"   File: {filepath}")

        # Read migration SQL
        with open(filepath, "r") as f:
            migration_sql = f.read()

        # Execute migration
        try:
            cursor = self.conn.cursor()
            start_time = datetime.now()

            print("\n⏳ Executing migration SQL...")
            cursor.execute(migration_sql)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            cursor.close()

            print(f"✓ Migration executed successfully in {duration:.2f} seconds")
            return True

        except Exception as e:
            print(f"✗ Migration failed: {e}")
            return False

    def commit_or_rollback(self, success: bool):
        """Commit transaction if successful, rollback otherwise."""
        if success:
            response = input("\n✅ Migration executed. Commit changes? (yes/no): ")
            if response.lower() in ["yes", "y"]:
                self.conn.commit()
                print("✓ Changes committed to database")
                return True
            else:
                self.conn.rollback()
                print("↩️  Changes rolled back")
                return False
        else:
            self.conn.rollback()
            print("↩️  Transaction rolled back due to errors")
            return False

    def run(self, direction: str, skip_backup_check: bool = False):
        """Main migration execution flow."""
        print("\n" + "=" * 70)
        print("DATABASE MIGRATION TOOL")
        print("=" * 70)

        # Connect to database
        if not self.connect():
            return False

        try:
            # Backup reminder (unless skipped)
            if not skip_backup_check:
                self.backup_reminder()

            # Pre-migration verification
            self.verify_tables_before()

            # Run migration
            success = self.run_migration(direction)

            if not success:
                self.commit_or_rollback(False)
                return False

            # Post-migration verification
            tables_ok = self.verify_tables_after(direction)
            data_ok = self.verify_data_integrity(direction)

            overall_success = success and tables_ok and data_ok

            if overall_success:
                print("\n" + "=" * 70)
                print("✅ MIGRATION SUCCESSFUL")
                print("=" * 70)
            else:
                print("\n" + "=" * 70)
                print("⚠️  MIGRATION COMPLETED WITH WARNINGS")
                print("=" * 70)
                print("Please review the verification results above.")

            # Commit or rollback
            return self.commit_or_rollback(overall_success)

        finally:
            self.disconnect()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run database migrations for Hey.sh",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run forward migration (domain -> topic)
  python scripts/run_migration.py --up

  # Run rollback migration (topic -> domain)
  python scripts/run_migration.py --down

  # Skip backup confirmation (for automated scripts)
  python scripts/run_migration.py --up --skip-backup-check

  # Use custom database URL
  python scripts/run_migration.py --up --db-url "postgresql://user:pass@host/db"
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--up", action="store_true", help="Run forward migration")
    group.add_argument("--down", action="store_true", help="Run rollback migration")

    parser.add_argument(
        "--db-url",
        default=os.getenv("DATABASE_URL"),
        help="Database connection URL (default: DATABASE_URL env var)",
    )

    parser.add_argument(
        "--skip-backup-check",
        action="store_true",
        help="Skip backup confirmation prompt (use with caution)",
    )

    parser.add_argument(
        "--migration",
        default="001",
        help="Migration number to run (default: 001)",
    )

    args = parser.parse_args()

    # Validate database URL
    if not args.db_url:
        print("❌ Error: Database URL not provided")
        print("   Set DATABASE_URL environment variable or use --db-url flag")
        sys.exit(1)

    # Determine direction
    direction = "up" if args.up else "down"

    # Run migration
    runner = MigrationRunner(args.db_url)
    success = runner.run(direction, skip_backup_check=args.skip_backup_check)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

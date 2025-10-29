#!/bin/bash
# Verification script for domain -> topic migration
# Run this after migration to verify everything is correct

set -e

echo "=========================================="
echo "Migration Verification Script"
echo "=========================================="
echo ""

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "❌ Error: psql not found. Please install PostgreSQL client."
    exit 1
fi

# Get database URL from environment or argument
DB_URL="${DATABASE_URL:-$1}"

if [ -z "$DB_URL" ]; then
    echo "❌ Error: No database URL provided"
    echo "   Usage: ./verify_migration.sh <database_url>"
    echo "   Or set DATABASE_URL environment variable"
    exit 1
fi

echo "🔍 Verifying migration..."
echo ""

# Function to run SQL query and show results
run_check() {
    local description=$1
    local query=$2

    echo "📋 $description"
    psql "$DB_URL" -c "$query" -t -A
    echo ""
}

# Check 1: Verify new tables exist
echo "✅ Check 1: New tables exist"
run_check "Topics table exists:" \
    "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'topics');"

run_check "Topic members table exists:" \
    "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'topic_members');"

# Check 2: Verify old tables are gone
echo "✅ Check 2: Old tables removed"
run_check "Domains table removed:" \
    "SELECT NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'domains');"

run_check "Domain members table removed:" \
    "SELECT NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'domain_members');"

# Check 3: Verify column renames
echo "✅ Check 3: Column renames"
run_check "Documents.topic_id exists:" \
    "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'documents' AND column_name = 'topic_id');"

run_check "Workflows.topic_id exists:" \
    "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'workflows' AND column_name = 'topic_id');"

# Check 4: Count records
echo "✅ Check 4: Record counts"
run_check "Topics count:" "SELECT COUNT(*) FROM topics;"
run_check "Topic members count:" "SELECT COUNT(*) FROM topic_members;"
run_check "Documents count:" "SELECT COUNT(*) FROM documents;"
run_check "Workflows count:" "SELECT COUNT(*) FROM workflows;"

# Check 5: Verify foreign keys
echo "✅ Check 5: Foreign key constraints"
psql "$DB_URL" << EOF
SELECT
  tc.constraint_name,
  tc.table_name,
  kcu.column_name,
  ccu.table_name AS foreign_table_name,
  ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_name IN ('documents', 'workflows', 'topic_members', 'membership_requests')
ORDER BY tc.table_name;
EOF

echo ""
echo "=========================================="
echo "✅ Verification complete!"
echo "=========================================="
echo ""
echo "Review the results above. All checks should return 't' (true)."
echo "Foreign keys should reference 'topics' table."

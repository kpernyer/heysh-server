# Migration Quick Start Guide

## Domain → Topic Migration

This guide provides step-by-step instructions for running the database migration from domain to topic terminology.

## Prerequisites

- [ ] PostgreSQL client tools installed (`psql`)
- [ ] Python 3.9+ with `psycopg2` package
- [ ] Database connection credentials
- [ ] **Full database backup created**
- [ ] All backend services stopped (API, workers, etc.)

## Quick Start (3 Steps)

### Step 1: Install Python Dependencies

```bash
pip install psycopg2-binary
```

### Step 2: Set Database URL

```bash
# Option A: Set environment variable
export DATABASE_URL="postgresql://user:password@host:port/database"

# Option B: Use Supabase connection string
export DATABASE_URL="postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres"
```

### Step 3: Run Migration

```bash
# Run forward migration (domain -> topic)
python scripts/run_migration.py --up

# If you need to rollback (topic -> domain)
python scripts/run_migration.py --down
```

## Detailed Instructions

### 1. Create Database Backup

**CRITICAL:** Always backup before migrations!

```bash
# Using pg_dump
pg_dump "$DATABASE_URL" > backup_$(date +%Y%m%d_%H%M%S).sql

# Using Supabase CLI
supabase db dump > backup.sql
```

### 2. Stop All Services

```bash
# Stop Docker containers
docker-compose down

# Or stop individual services
pkill -f "uvicorn.*api"
pkill -f "python.*worker"
```

### 3. Run Migration with Python Script

The Python script provides:
- Pre-migration verification
- Safe transaction handling
- Post-migration verification
- Data integrity checks
- Rollback on errors

```bash
# Forward migration
python scripts/run_migration.py --up

# The script will:
# 1. Prompt for confirmation
# 2. Show pre-migration state
# 3. Execute migration
# 4. Verify results
# 5. Ask to commit or rollback
```

### 4. Verify Migration

```bash
# Automated verification
./scripts/verify_migration.sh "$DATABASE_URL"

# Manual verification
psql "$DATABASE_URL" << EOF
-- Check tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('topics', 'topic_members');

-- Check record counts
SELECT
  (SELECT COUNT(*) FROM topics) as topics,
  (SELECT COUNT(*) FROM topic_members) as members,
  (SELECT COUNT(*) FROM documents) as documents;
EOF
```

### 5. Restart Services

```bash
# Using Docker
docker-compose up -d

# Or manually
uvicorn src.service.api:app --reload
```

## Alternative Methods

### Method 1: Direct SQL Execution

```bash
# Using psql
psql "$DATABASE_URL" < migrations/001_rename_domain_to_topic_up.sql

# Verify
./scripts/verify_migration.sh "$DATABASE_URL"
```

### Method 2: Supabase Dashboard

1. Go to your Supabase project
2. Navigate to **SQL Editor**
3. Copy contents of `migrations/001_rename_domain_to_topic_up.sql`
4. Click **Run**
5. Verify in Table Editor that `topics` and `topic_members` exist

### Method 3: Supabase CLI

```bash
# Link project
supabase link --project-ref your-project-ref

# Run migration
supabase db push migrations/001_rename_domain_to_topic_up.sql
```

## Rollback Instructions

If something goes wrong:

### Automatic Rollback (Recommended)

```bash
python scripts/run_migration.py --down
```

### Manual Rollback

```bash
# Using psql
psql "$DATABASE_URL" < migrations/001_rename_domain_to_topic_down.sql

# Or restore from backup
psql "$DATABASE_URL" < backup_YYYYMMDD_HHMMSS.sql
```

## Verification Checklist

After migration, verify:

- [ ] `topics` table exists and contains data
- [ ] `topic_members` table exists and contains data
- [ ] `domains` table no longer exists
- [ ] `domain_members` table no longer exists
- [ ] `documents.topic_id` column exists
- [ ] `workflows.topic_id` column exists
- [ ] Foreign keys reference `topics` table
- [ ] Record counts match pre-migration counts
- [ ] Backend API starts without errors
- [ ] Frontend can connect and fetch topics

## Common Issues

### Issue: Migration fails with "table already exists"

**Solution:** Check if migration was partially applied:

```sql
SELECT table_name FROM information_schema.tables
WHERE table_name IN ('topics', 'topic_members', 'domains', 'domain_members');
```

If you have both old and new tables, manually drop the new ones and retry.

### Issue: Foreign key constraint errors

**Solution:** Ensure no active connections:

```sql
-- Check active connections
SELECT * FROM pg_stat_activity WHERE datname = current_database();

-- Terminate connections if needed (careful!)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = current_database()
AND pid <> pg_backend_pid();
```

### Issue: Permission denied

**Solution:** Ensure you're using a superuser or have ALTER TABLE privileges:

```sql
-- Check current user
SELECT current_user;

-- Grant privileges if needed
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
```

### Issue: Data appears missing after migration

**Immediate action:**
1. **DO NOT PANIC**
2. Run rollback immediately
3. Restore from backup
4. Contact database administrator

```bash
# Rollback
python scripts/run_migration.py --down

# Restore from backup
psql "$DATABASE_URL" < backup_YYYYMMDD_HHMMSS.sql
```

## Post-Migration Tasks

After successful migration:

1. **Update Backend Code** (already done)
   - API routes use `/topics` endpoints
   - Request models use `topic_id` fields

2. **Update Frontend Code**
   - Update API client functions
   - Change `domain_id` to `topic_id` in requests
   - Update endpoint URLs

3. **Update Documentation**
   - API documentation
   - Database schema diagrams
   - User guides

4. **Monitor Application**
   - Check logs for errors
   - Monitor database performance
   - Verify user workflows

5. **Update Development Environments**
   - Run migration in dev/staging
   - Update seed data scripts
   - Update test fixtures

## Environment-Specific Instructions

### Local Development

```bash
# Assuming Docker Compose database
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/heysh"
python scripts/run_migration.py --up --skip-backup-check
```

### Staging

```bash
export DATABASE_URL="<staging-db-url>"
python scripts/run_migration.py --up
```

### Production

```bash
# 1. Schedule maintenance window
# 2. Notify users
# 3. Create backup
# 4. Stop services
# 5. Run migration

export DATABASE_URL="<production-db-url>"
python scripts/run_migration.py --up

# 6. Verify thoroughly
./scripts/verify_migration.sh "$DATABASE_URL"

# 7. Restart services
# 8. Monitor closely
```

## Support

If you encounter issues:

1. Check the [detailed README](migrations/README.md)
2. Review verification queries in the README
3. Check migration logs
4. Restore from backup if needed
5. Contact the backend team

## Estimated Timeline

- **Development:** 5-10 minutes
- **Staging:** 15-30 minutes
- **Production:** 30-60 minutes (with full verification)

## Safety Notes

- ✅ **DO** create backups before migration
- ✅ **DO** test in staging first
- ✅ **DO** stop all services during migration
- ✅ **DO** verify data integrity after migration
- ❌ **DON'T** run migration during peak hours
- ❌ **DON'T** skip verification steps
- ❌ **DON'T** ignore warnings or errors
- ❌ **DON'T** modify migration scripts without testing

## Success Criteria

Migration is successful when:

1. All verification checks pass (green checkmarks)
2. Record counts match pre-migration state
3. Backend API starts without errors
4. Frontend can query topics
5. No error logs related to database schema
6. All foreign key relationships intact

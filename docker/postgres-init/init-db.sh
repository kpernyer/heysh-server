#!/bin/bash
set -e

# Create business database (Temporal uses 'temporal' database)
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create business database
    CREATE DATABASE heysh;

    -- Grant permissions
    GRANT ALL PRIVILEGES ON DATABASE heysh TO temporal;
EOSQL

echo "✅ Business database 'heysh' created successfully"

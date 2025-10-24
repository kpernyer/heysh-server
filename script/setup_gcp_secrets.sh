#!/bin/bash
# Setup GCP secrets for hey-sh deployment
# This script creates all required secrets in Google Secret Manager

set -e

echo "🔐 Setting up GCP Secrets for Hey.sh"
echo "======================================"
echo ""

# Check if gcloud is configured
if ! gcloud config get-value project &>/dev/null; then
    echo "❌ Error: No GCP project configured"
    echo "   Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

PROJECT_ID=$(gcloud config get-value project)
echo "📦 Project: $PROJECT_ID"
echo ""

# Load environment variables
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    exit 1
fi

set -a
source .env
set +a

# Function to create or update a secret
create_secret() {
    local secret_name=$1
    local secret_value=$2

    if [ -z "$secret_value" ]; then
        echo "⚠️  Skipping $secret_name (not set in .env)"
        return
    fi

    # Check if secret exists
    if gcloud secrets describe "$secret_name" &>/dev/null; then
        echo "🔄 Updating existing secret: $secret_name"
        echo -n "$secret_value" | gcloud secrets versions add "$secret_name" --data-file=-
    else
        echo "✨ Creating new secret: $secret_name"
        echo -n "$secret_value" | gcloud secrets create "$secret_name" --data-file=-
    fi

    echo "   ✅ $secret_name configured"
}

echo "📝 Creating/updating secrets..."
echo ""

# Temporal secrets
create_secret "temporal-api-key" "$TEMPORAL_API_KEY"
create_secret "temporal-namespace" "$TEMPORAL_NAMESPACE"
create_secret "temporal-address" "$TEMPORAL_ADDRESS"

# Neo4j secrets
create_secret "neo4j-uri" "$NEO4J_URI"
create_secret "neo4j-user" "$NEO4J_USER"
create_secret "neo4j-password" "$NEO4J_PASSWORD"

# Weaviate secrets
create_secret "weaviate-url" "$WEAVIATE_URL"
create_secret "weaviate-api-key" "$WEAVIATE_API_KEY"
create_secret "weaviate-grpc-host" "$WEAVIATE_GRPC_HOST"

# OpenAI secret
create_secret "openai-api-key" "$OPENAI_API_KEY"

# Supabase secrets
create_secret "supabase-url" "$SUPABASE_URL"
create_secret "supabase-key" "$SUPABASE_KEY"

echo ""
echo "🔑 Granting access to Cloud Run service account..."
echo ""

# Get the default compute service account
SERVICE_ACCOUNT="${PROJECT_ID//[^0-9]/}-compute@developer.gserviceaccount.com"
echo "   Service account: $SERVICE_ACCOUNT"
echo ""

# Grant access to all secrets
for secret in temporal-api-key temporal-namespace temporal-address \
              neo4j-uri neo4j-user neo4j-password \
              weaviate-url weaviate-api-key weaviate-grpc-host \
              openai-api-key supabase-url supabase-key; do

    # Check if secret exists before granting access
    if gcloud secrets describe "$secret" &>/dev/null; then
        echo "   Granting access to: $secret"
        gcloud secrets add-iam-policy-binding "$secret" \
            --member="serviceAccount:$SERVICE_ACCOUNT" \
            --role="roles/secretmanager.secretAccessor" \
            --quiet
    fi
done

echo ""
echo "✅ All secrets configured successfully!"
echo ""
echo "📋 Summary of created secrets:"
gcloud secrets list --format="table(name,created)"
echo ""
echo "🎯 Next steps:"
echo "   1. Deploy worker: ./script/deploy_worker.sh"
echo "   2. Deploy backend: ./script/deploy_backend.sh"
echo "   3. Verify deployments in Cloud Console"
echo ""

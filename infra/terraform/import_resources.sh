#!/bin/bash
echo "Importing existing resources..."

# Import GKE cluster
echo "Importing GKE cluster..."
terraform import google_container_cluster.hey_sh_cluster projects/hey-sh-production/locations/europe-west3/clusters/development-hey-sh-cluster 2>/dev/null || echo "Cluster already imported"

# Import secrets
SECRETS=(
    "SUPABASE_URL"
    "SUPABASE_KEY"
    "TEMPORAL_ADDRESS"
    "TEMPORAL_NAMESPACE"
    "TEMPORAL_API_KEY"
    "TEMPORAL_TASK_QUEUE"
    "NEO4J_URI"
    "NEO4J_USER"
    "NEO4J_PASSWORD"
    "WEAVIATE_URL"
    "WEAVIATE_API_KEY"
    "OPENAI_API_KEY"
    "ANTHROPIC_API_KEY"
    "GOOGLE_CLOUD_PROJECT"
)

for secret in "${SECRETS[@]}"; do
    echo "Importing secret $secret..."
    terraform import google_secret_manager_secret.${secret,,} $secret 2>/dev/null || echo "Secret $secret already imported or doesn't exist"
done

echo "Import complete!"

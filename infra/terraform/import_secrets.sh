#!/bin/bash

# Import all secrets into Terraform state
secrets=(
    "supabase_url:SUPABASE_URL"
    "supabase_key:SUPABASE_KEY"
    "temporal_address:TEMPORAL_ADDRESS"
    "temporal_namespace:TEMPORAL_NAMESPACE"
    "temporal_api_key:TEMPORAL_API_KEY"
    "temporal_task_queue:TEMPORAL_TASK_QUEUE"
    "neo4j_uri:NEO4J_URI"
    "neo4j_user:NEO4J_USER"
    "neo4j_password:NEO4J_PASSWORD"
    "weaviate_url:WEAVIATE_URL"
    "weaviate_api_key:WEAVIATE_API_KEY"
    "openai_api_key:OPENAI_API_KEY"
    "anthropic_api_key:ANTHROPIC_API_KEY"
    "google_cloud_project:GOOGLE_CLOUD_PROJECT"
)

for secret_pair in "${secrets[@]}"; do
    IFS=':' read -r tf_name gcp_name <<< "$secret_pair"
    echo "Importing $gcp_name..."
    terraform import google_secret_manager_secret.$tf_name $gcp_name 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Imported $gcp_name"
    else
        echo "⚠️  $gcp_name already in state or doesn't exist"
    fi
done

echo "Import complete!"
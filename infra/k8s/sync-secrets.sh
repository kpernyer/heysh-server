#!/bin/bash

# Script to sync secrets from GCP Secret Manager to Kubernetes

PROJECT_ID="hey-sh-production"
NAMESPACE="hey-sh"

echo "Syncing secrets from GCP Secret Manager to Kubernetes..."

# Get cluster credentials
echo "Getting cluster credentials..."
gcloud container clusters get-credentials development-hey-sh-cluster --region europe-west3 --project $PROJECT_ID

# Create namespace if it doesn't exist
kubectl create namespace $NAMESPACE 2>/dev/null || echo "Namespace already exists"

# Function to get secret value from Secret Manager
get_secret_value() {
    local secret_name=$1
    gcloud secrets versions access latest --secret=$secret_name --project=$PROJECT_ID 2>/dev/null || echo ""
}

# Temporal secrets
echo "Creating Temporal secrets..."
kubectl create secret generic temporal-secrets \
  --namespace=$NAMESPACE \
  --from-literal=address="$(get_secret_value TEMPORAL_ADDRESS)" \
  --from-literal=namespace="$(get_secret_value TEMPORAL_NAMESPACE)" \
  --from-literal=api-key="$(get_secret_value TEMPORAL_API_KEY)" \
  --from-literal=task-queue="$(get_secret_value TEMPORAL_TASK_QUEUE)" \
  --dry-run=client -o yaml | kubectl apply -f -

# Supabase secrets
echo "Creating Supabase secrets..."
kubectl create secret generic supabase-secrets \
  --namespace=$NAMESPACE \
  --from-literal=url="$(get_secret_value SUPABASE_URL)" \
  --from-literal=key="$(get_secret_value SUPABASE_KEY)" \
  --dry-run=client -o yaml | kubectl apply -f -

# Neo4j secrets
echo "Creating Neo4j secrets..."
kubectl create secret generic neo4j-secrets \
  --namespace=$NAMESPACE \
  --from-literal=uri="$(get_secret_value NEO4J_URI)" \
  --from-literal=user="$(get_secret_value NEO4J_USER)" \
  --from-literal=password="$(get_secret_value NEO4J_PASSWORD)" \
  --dry-run=client -o yaml | kubectl apply -f -

# Weaviate secrets
echo "Creating Weaviate secrets..."
kubectl create secret generic weaviate-secrets \
  --namespace=$NAMESPACE \
  --from-literal=url="$(get_secret_value WEAVIATE_URL)" \
  --from-literal=api-key="$(get_secret_value WEAVIATE_API_KEY)" \
  --dry-run=client -o yaml | kubectl apply -f -

# LLM secrets
echo "Creating LLM secrets..."
kubectl create secret generic llm-secrets \
  --namespace=$NAMESPACE \
  --from-literal=openai-api-key="$(get_secret_value OPENAI_API_KEY)" \
  --from-literal=anthropic-api-key="$(get_secret_value ANTHROPIC_API_KEY)" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Secrets sync complete!"
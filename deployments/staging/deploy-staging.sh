#!/bin/bash

# Deploy to staging environment in Google Cloud
# This script sets up a complete staging environment for testing

set -e

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-"hey-sh-workflow-staging"}
REGION=${GCP_REGION:-"europe-north1"}
CLUSTER_NAME="staging-temporal-cluster"
TEMPORAL_NAMESPACE="staging"
VERSION=${VERSION:-$(git rev-parse --short HEAD)}

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Deploying to Staging Environment${NC}"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Version: $VERSION"

# 1. Authenticate and set project
echo -e "${GREEN}📦 Setting up GCP project...${NC}"
gcloud config set project $PROJECT_ID
gcloud auth configure-docker

# 2. Create GKE cluster if it doesn't exist
if ! gcloud container clusters describe $CLUSTER_NAME --region=$REGION &>/dev/null; then
    echo -e "${GREEN}🔧 Creating GKE cluster...${NC}"
    gcloud container clusters create $CLUSTER_NAME \
        --region=$REGION \
        --num-nodes=2 \
        --node-pool=default-pool \
        --machine-type=e2-standard-4 \
        --enable-autoscaling \
        --min-nodes=2 \
        --max-nodes=10 \
        --enable-autorepair \
        --enable-stackdriver-kubernetes

    # Create GPU node pool for AI workers
    gcloud container node-pools create ai-pool \
        --cluster=$CLUSTER_NAME \
        --region=$REGION \
        --machine-type=n1-standard-4 \
        --accelerator="type=nvidia-tesla-t4,count=1" \
        --num-nodes=1 \
        --min-nodes=0 \
        --max-nodes=3 \
        --enable-autoscaling \
        --node-taints="workload-type=gpu:NoSchedule" \
        --node-labels="workload-type=gpu"

    # Create storage-optimized node pool
    gcloud container node-pools create storage-pool \
        --cluster=$CLUSTER_NAME \
        --region=$REGION \
        --machine-type=n2-standard-4 \
        --num-nodes=2 \
        --min-nodes=1 \
        --max-nodes=5 \
        --enable-autoscaling \
        --disk-type=pd-ssd \
        --disk-size=100 \
        --node-labels="workload-type=storage-optimized"
fi

# 3. Get cluster credentials
echo -e "${GREEN}🔐 Getting cluster credentials...${NC}"
gcloud container clusters get-credentials $CLUSTER_NAME --region=$REGION

# 4. Install Temporal (if not exists)
if ! kubectl get namespace temporal-system &>/dev/null; then
    echo -e "${GREEN}⚙️ Installing Temporal...${NC}"

    # Add Temporal Helm repo
    helm repo add temporal https://temporalio.github.io/helm-charts
    helm repo update

    # Install Temporal
    helm install temporal temporal/temporal \
        --namespace temporal-system \
        --create-namespace \
        --set server.replicaCount=3 \
        --set cassandra.config.cluster_size=3 \
        --set prometheus.enabled=true \
        --set grafana.enabled=true \
        --set elasticsearch.enabled=true \
        --wait
fi

# 5. Deploy databases (Weaviate & Neo4j)
echo -e "${GREEN}🗄️ Deploying databases...${NC}"

# Deploy Weaviate
helm repo add weaviate https://weaviate.github.io/weaviate-helm
helm upgrade --install weaviate weaviate/weaviate \
    --namespace databases \
    --create-namespace \
    --set replicas=2 \
    --set resources.requests.memory=2Gi \
    --set resources.limits.memory=4Gi

# Deploy Neo4j
helm repo add neo4j https://neo4j.github.io/neo4j-helm
helm upgrade --install neo4j neo4j/neo4j \
    --namespace databases \
    --set core.standalone=false \
    --set core.numberOfServers=3 \
    --set auth.enabled=true \
    --set auth.password=$NEO4J_PASSWORD

# 6. Build and push Docker images
echo -e "${GREEN}🐳 Building and pushing Docker images...${NC}"

# Build images
docker build -t gcr.io/$PROJECT_ID/hey-sh-worker:$VERSION -f Dockerfile .
docker build -t gcr.io/$PROJECT_ID/hey-sh-ai-worker:$VERSION -f deployments/Dockerfile.ai-worker .
docker build -t gcr.io/$PROJECT_ID/hey-sh-storage-worker:$VERSION -f deployments/Dockerfile.storage-worker .

# Push images
docker push gcr.io/$PROJECT_ID/hey-sh-worker:$VERSION
docker push gcr.io/$PROJECT_ID/hey-sh-ai-worker:$VERSION
docker push gcr.io/$PROJECT_ID/hey-sh-storage-worker:$VERSION

# 7. Create secrets
echo -e "${GREEN}🔒 Creating secrets...${NC}"
kubectl create namespace temporal-workers --dry-run=client -o yaml | kubectl apply -f -

# Create secrets from environment
kubectl create secret generic database-credentials \
    --namespace=temporal-workers \
    --from-literal=supabase-url=$STAGING_SUPABASE_URL \
    --from-literal=supabase-key=$STAGING_SUPABASE_KEY \
    --from-literal=neo4j-user=neo4j \
    --from-literal=neo4j-password=$NEO4J_PASSWORD \
    --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic ai-credentials \
    --namespace=temporal-workers \
    --from-literal=openai-api-key=$OPENAI_API_KEY \
    --from-literal=anthropic-api-key=$ANTHROPIC_API_KEY \
    --dry-run=client -o yaml | kubectl apply -f -

# 8. Deploy workers
echo -e "${GREEN}🚀 Deploying workers...${NC}"

# Update image tags in manifests
export REGISTRY="gcr.io/$PROJECT_ID"
export VERSION=$VERSION

# Apply manifests
envsubst < k8s/configmaps.yaml | kubectl apply -f -
envsubst < k8s/ai-worker-deployment.yaml | kubectl apply -f -
envsubst < k8s/storage-worker-deployment.yaml | kubectl apply -f -
envsubst < k8s/general-worker-deployment.yaml | kubectl apply -f -

# 9. Wait for deployments
echo -e "${YELLOW}⏳ Waiting for deployments to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s \
    deployment/general-worker \
    deployment/storage-worker \
    deployment/ai-processing-worker \
    -n temporal-workers

# 10. Run smoke tests
echo -e "${GREEN}🧪 Running smoke tests...${NC}"
python test/smoke_test_staging.py

# 11. Setup monitoring
echo -e "${GREEN}📊 Setting up monitoring...${NC}"

# Create Cloud Monitoring dashboard
gcloud monitoring dashboards create --config-from-file=monitoring/dashboard.json

# Create alerts
gcloud alpha monitoring policies create --policy-from-file=monitoring/alerts.yaml

# 12. Print access information
echo -e "${GREEN}✅ Staging deployment complete!${NC}"
echo ""
echo "Access URLs:"
echo "  Temporal Web UI: http://$(kubectl get svc temporal-web -n temporal-system -o jsonpath='{.status.loadBalancer.ingress[0].ip}'):8088"
echo "  Grafana: http://$(kubectl get svc temporal-grafana -n temporal-system -o jsonpath='{.status.loadBalancer.ingress[0].ip}'):3000"
echo "  Weaviate: http://$(kubectl get svc weaviate -n databases -o jsonpath='{.status.loadBalancer.ingress[0].ip}'):8080"
echo ""
echo "To view worker logs:"
echo "  kubectl logs -n temporal-workers -l worker-type=ai-processing -f"
echo "  kubectl logs -n temporal-workers -l worker-type=storage -f"
echo "  kubectl logs -n temporal-workers -l worker-type=general -f"

#!/bin/bash
# Unified deployment script using Terraform + Helm
# This is the proper way to deploy infrastructure and applications

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${ENVIRONMENT:-production}
REGION=${REGION:-europe-west3}
VERSION=${VERSION:-$(git rev-parse --short HEAD)}
DEPLOY_BACKEND=${DEPLOY_BACKEND:-true}
DEPLOY_WORKERS=${DEPLOY_WORKERS:-true}
SKIP_TERRAFORM=${SKIP_TERRAFORM:-false}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Hey.sh Deployment Pipeline${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Environment:${NC} $ENVIRONMENT"
echo -e "${GREEN}Region:${NC} $REGION"
echo -e "${GREEN}Version:${NC} $VERSION"
echo -e "${GREEN}Deploy Backend:${NC} $DEPLOY_BACKEND"
echo -e "${GREEN}Deploy Workers:${NC} $DEPLOY_WORKERS"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found${NC}"
    exit 1
fi

if ! command -v terraform &> /dev/null; then
    echo -e "${RED}Error: terraform not found${NC}"
    exit 1
fi

if [ "$DEPLOY_WORKERS" = "true" ] && ! command -v helm &> /dev/null; then
    echo -e "${RED}Error: helm not found${NC}"
    exit 1
fi

if [ "$DEPLOY_WORKERS" = "true" ] && ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl not found${NC}"
    exit 1
fi

# Get GCP project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: No GCP project configured${NC}"
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo -e "${GREEN}✓ Project: $PROJECT_ID${NC}"
echo ""

# Step 1: Apply Terraform (Infrastructure as Code)
if [ "$SKIP_TERRAFORM" != "true" ]; then
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} Step 1: Applying Terraform${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    cd infra/terraform

    echo -e "${YELLOW}Initializing Terraform...${NC}"
    terraform init

    echo -e "${YELLOW}Planning Terraform changes...${NC}"
    terraform plan \
        -var="project_id=$PROJECT_ID" \
        -var="region=$REGION" \
        -var="environment=$ENVIRONMENT" \
        -out=tfplan

    echo ""
    echo -e "${YELLOW}Apply these changes? (yes/no)${NC}"
    read -r APPLY_TERRAFORM

    if [ "$APPLY_TERRAFORM" = "yes" ]; then
        echo -e "${YELLOW}Applying Terraform...${NC}"
        terraform apply tfplan
        echo -e "${GREEN}✓ Terraform applied successfully${NC}"
    else
        echo -e "${YELLOW}Skipping Terraform apply${NC}"
    fi

    cd ../..
    echo ""
else
    echo -e "${YELLOW}Skipping Terraform (SKIP_TERRAFORM=true)${NC}"
    echo ""
fi

# Step 2: Build and deploy Backend API
if [ "$DEPLOY_BACKEND" = "true" ]; then
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} Step 2: Building Backend API${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    echo -e "${YELLOW}Building Docker image via Cloud Build...${NC}"
    gcloud builds submit \
        --config cloudbuild_backend.yaml \
        --project "$PROJECT_ID" \
        --substitutions="_VERSION=$VERSION,_REGION=$REGION"

    echo -e "${GREEN}✓ Backend API image built${NC}"

    echo -e "${YELLOW}Updating Cloud Run service...${NC}"
    # The Cloud Run service is managed by Terraform, but we can trigger a new revision
    # by updating the image tag through Terraform or using gcloud
    # For now, we'll use gcloud to update the image (Terraform manages the rest)

    SERVICE_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/hey-sh-backend/service:${VERSION}"

    gcloud run services update api \
        --image "$SERVICE_IMAGE" \
        --region "$REGION" \
        --project "$PROJECT_ID"

    SERVICE_URL=$(gcloud run services describe api --region "$REGION" --format "value(status.url)" --project "$PROJECT_ID")
    echo ""
    echo -e "${GREEN}✓ Backend API deployed${NC}"
    echo -e "${GREEN}  URL: $SERVICE_URL${NC}"
    echo ""
else
    echo -e "${YELLOW}Skipping backend deployment (DEPLOY_BACKEND=false)${NC}"
    echo ""
fi

# Step 3: Build and deploy Workers to GKE
if [ "$DEPLOY_WORKERS" = "true" ]; then
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} Step 3: Building Worker Images${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    echo -e "${YELLOW}Building worker images via Cloud Build...${NC}"
    gcloud builds submit \
        --config cloudbuild_workers.yaml \
        --project "$PROJECT_ID" \
        --substitutions="_VERSION=$VERSION,_REGION=$REGION"

    echo -e "${GREEN}✓ Worker images built${NC}"
    echo ""

    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} Step 4: Deploying Workers via Helm${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    # Get GKE cluster credentials
    CLUSTER_NAME="${ENVIRONMENT}-hey-sh-cluster"
    echo -e "${YELLOW}Getting GKE cluster credentials...${NC}"
    gcloud container clusters get-credentials "$CLUSTER_NAME" \
        --region "$REGION" \
        --project "$PROJECT_ID"

    echo -e "${GREEN}✓ Connected to cluster: $CLUSTER_NAME${NC}"

    # Sync secrets from GCP Secret Manager to Kubernetes
    echo -e "${YELLOW}Syncing secrets from GCP Secret Manager...${NC}"
    ./infra/k8s/sync-secrets.sh

    # Deploy workers using Helm
    echo -e "${YELLOW}Deploying workers via Helm...${NC}"

    TEMPORAL_ADDRESS=$(gcloud secrets versions access latest --secret=TEMPORAL_ADDRESS --project="$PROJECT_ID" 2>/dev/null || echo "")
    TEMPORAL_NAMESPACE=$(gcloud secrets versions access latest --secret=TEMPORAL_NAMESPACE --project="$PROJECT_ID" 2>/dev/null || echo "default")

    helm upgrade --install temporal-workers ./infra/helm/temporal-workers \
        --namespace temporal-workers \
        --create-namespace \
        --set global.projectId="$PROJECT_ID" \
        --set global.region="$REGION" \
        --set global.environment="$ENVIRONMENT" \
        --set image.repository="${PROJECT_ID}/hey-sh-backend" \
        --set image.tag="$VERSION" \
        --set temporal.address="$TEMPORAL_ADDRESS" \
        --set temporal.namespace="$TEMPORAL_NAMESPACE" \
        --wait \
        --timeout 10m

    echo -e "${GREEN}✓ Workers deployed via Helm${NC}"
    echo ""

    # Show deployment status
    echo -e "${YELLOW}Checking deployment status...${NC}"
    kubectl get pods -n temporal-workers -l app=temporal-worker

    echo ""
    echo -e "${GREEN}To view worker logs:${NC}"
    echo "  kubectl logs -n temporal-workers -l worker-type=ai-processing -f"
    echo "  kubectl logs -n temporal-workers -l worker-type=storage -f"
    echo "  kubectl logs -n temporal-workers -l worker-type=general -f"
    echo ""
else
    echo -e "${YELLOW}Skipping worker deployment (DEPLOY_WORKERS=false)${NC}"
    echo ""
fi

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Deployment Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Deployed components:${NC}"
[ "$DEPLOY_BACKEND" = "true" ] && echo -e "  ${GREEN}✓${NC} Backend API (Cloud Run)"
[ "$DEPLOY_WORKERS" = "true" ] && echo -e "  ${GREEN}✓${NC} Workers (GKE + Helm)"
echo ""
echo -e "${GREEN}Infrastructure managed by:${NC}"
echo -e "  ${GREEN}✓${NC} Terraform (GCP resources)"
echo -e "  ${GREEN}✓${NC} Helm (Kubernetes workloads)"
echo ""

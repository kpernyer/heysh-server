#!/bin/bash
# Production Deployment Script for Hey.sh Backend
# Includes: Database Migration + Terraform + Backend + Workers

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Hey.sh Production Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Configuration
ENVIRONMENT=${ENVIRONMENT:-production}
REGION=${REGION:-europe-west3}
VERSION=${VERSION:-$(git rev-parse --short HEAD 2>/dev/null || echo "latest")}
RUN_MIGRATION=${RUN_MIGRATION:-true}
SKIP_TERRAFORM=${SKIP_TERRAFORM:-false}

echo -e "${GREEN}Configuration:${NC}"
echo -e "  Environment: $ENVIRONMENT"
echo -e "  Region: $REGION"
echo -e "  Version: $VERSION"
echo -e "  Run Migration: $RUN_MIGRATION"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

MISSING_TOOLS=()
command -v gcloud &> /dev/null || MISSING_TOOLS+=("gcloud")
command -v terraform &> /dev/null || MISSING_TOOLS+=("terraform")
command -v helm &> /dev/null || MISSING_TOOLS+=("helm")
command -v kubectl &> /dev/null || MISSING_TOOLS+=("kubectl")

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    echo -e "${RED}Error: Missing required tools: ${MISSING_TOOLS[*]}${NC}"
    exit 1
fi

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: No GCP project configured${NC}"
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo -e "${GREEN}✓ Project: $PROJECT_ID${NC}"
echo ""

# ============================================================================
# STEP 0: Database Migration (if needed)
# ============================================================================
if [ "$RUN_MIGRATION" = "true" ]; then
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} Step 0: Database Migration${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    echo -e "${YELLOW}⚠️  IMPORTANT: Database Migration${NC}"
    echo -e "This will rename 'domains' → 'topics' in the database."
    echo -e ""
    echo -e "Changes:"
    echo -e "  • Tables: domains → topics, domain_members → topic_members"
    echo -e "  • Columns: domain_id → topic_id in all related tables"
    echo -e "  • Foreign keys and indexes updated"
    echo -e ""
    echo -e "${YELLOW}Do you want to run the database migration? (yes/no)${NC}"
    read -r RUN_MIGRATION_CONFIRM

    if [ "$RUN_MIGRATION_CONFIRM" = "yes" ]; then
        echo -e "${YELLOW}Running database migration...${NC}"

        # Get Supabase connection URL from Secret Manager
        SUPABASE_URL=$(gcloud secrets versions access latest --secret=SUPABASE_URL --project="$PROJECT_ID" 2>/dev/null || echo "")

        if [ -z "$SUPABASE_URL" ]; then
            echo -e "${RED}Error: Could not retrieve SUPABASE_URL from Secret Manager${NC}"
            echo -e "${YELLOW}Please run migration manually:${NC}"
            echo -e "  1. Go to Supabase Dashboard → SQL Editor"
            echo -e "  2. Run: migrations/001_rename_domain_to_topic_up.sql"
            echo -e ""
            echo -e "${YELLOW}Continue without migration? (yes/no)${NC}"
            read -r CONTINUE_WITHOUT_MIGRATION
            if [ "$CONTINUE_WITHOUT_MIGRATION" != "yes" ]; then
                exit 1
            fi
        else
            echo -e "${GREEN}✓ Database connection available${NC}"
            echo -e "${YELLOW}Migration must be run manually via Supabase Dashboard${NC}"
            echo -e ""
            echo -e "Steps:"
            echo -e "  1. Open: $SUPABASE_URL"
            echo -e "  2. Navigate to SQL Editor"
            echo -e "  3. Copy & paste: migrations/001_rename_domain_to_topic_up.sql"
            echo -e "  4. Click 'Run'"
            echo -e ""
            echo -e "${YELLOW}Have you completed the migration? (yes/no)${NC}"
            read -r MIGRATION_COMPLETED
            if [ "$MIGRATION_COMPLETED" != "yes" ]; then
                echo -e "${RED}Please complete the migration before continuing${NC}"
                exit 1
            fi
            echo -e "${GREEN}✓ Migration confirmed${NC}"
        fi
    else
        echo -e "${YELLOW}Skipping database migration${NC}"
        echo -e "${RED}⚠️  WARNING: Frontend will expect topic terminology!${NC}"
    fi
    echo ""
fi

# ============================================================================
# STEP 1: Terraform (Infrastructure)
# ============================================================================
if [ "$SKIP_TERRAFORM" != "true" ]; then
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} Step 1: Terraform Infrastructure${NC}"
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
    echo -e "${YELLOW}Apply Terraform changes? (yes/no)${NC}"
    read -r APPLY_TERRAFORM

    if [ "$APPLY_TERRAFORM" = "yes" ]; then
        terraform apply tfplan
        echo -e "${GREEN}✓ Terraform applied${NC}"
    else
        echo -e "${YELLOW}Skipping Terraform${NC}"
    fi

    cd ../..
    echo ""
else
    echo -e "${YELLOW}Skipping Terraform (SKIP_TERRAFORM=true)${NC}"
    echo ""
fi

# ============================================================================
# STEP 2: Build & Deploy Backend API
# ============================================================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE} Step 2: Backend API (Cloud Run)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}Building Docker image...${NC}"
gcloud builds submit \
    --config cloudbuild_backend.yaml \
    --project "$PROJECT_ID" \
    --substitutions="_VERSION=$VERSION,_REGION=$REGION"

echo -e "${GREEN}✓ Backend image built${NC}"

SERVICE_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/hey-sh-backend/service:${VERSION}"

echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
gcloud run services update api \
    --image "$SERVICE_IMAGE" \
    --region "$REGION" \
    --project "$PROJECT_ID"

SERVICE_URL=$(gcloud run services describe api --region "$REGION" --format "value(status.url)" --project "$PROJECT_ID" 2>/dev/null || echo "")

echo -e "${GREEN}✓ Backend deployed${NC}"
if [ -n "$SERVICE_URL" ]; then
    echo -e "${GREEN}  URL: $SERVICE_URL${NC}"
fi
echo ""

# ============================================================================
# STEP 3: Build & Deploy Workers (GKE + Helm)
# ============================================================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE} Step 3: Workers (GKE + Helm)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}Building worker images...${NC}"
gcloud builds submit \
    --config cloudbuild_workers.yaml \
    --project "$PROJECT_ID" \
    --substitutions="_VERSION=$VERSION,_REGION=$REGION"

echo -e "${GREEN}✓ Worker images built${NC}"

# Get cluster credentials
CLUSTER_NAME="${ENVIRONMENT}-hey-sh-cluster"
echo -e "${YELLOW}Connecting to GKE cluster...${NC}"
gcloud container clusters get-credentials "$CLUSTER_NAME" \
    --region "$REGION" \
    --project "$PROJECT_ID"

echo -e "${GREEN}✓ Connected to: $CLUSTER_NAME${NC}"

# Sync secrets
echo -e "${YELLOW}Syncing secrets from GCP Secret Manager...${NC}"
./infra/k8s/sync-secrets.sh 2>/dev/null || echo "Warning: Could not sync secrets automatically"

# Deploy via Helm
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

echo -e "${GREEN}✓ Workers deployed${NC}"

# Show status
echo -e "${YELLOW}Worker pods:${NC}"
kubectl get pods -n temporal-workers -l app=temporal-worker

echo ""

# ============================================================================
# DEPLOYMENT COMPLETE
# ============================================================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Deployment Complete! 🎉${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${GREEN}Deployed components:${NC}"
echo -e "  ✓ Backend API (Cloud Run)"
echo -e "  ✓ Workers (GKE + Helm)"
[ "$RUN_MIGRATION" = "true" ] && echo -e "  ✓ Database Migration"
echo ""

if [ -n "$SERVICE_URL" ]; then
    echo -e "${GREEN}Backend API:${NC}"
    echo -e "  URL: $SERVICE_URL"
    echo -e "  Health: $SERVICE_URL/health"
    echo -e "  API: $SERVICE_URL/api/v1/topics"
    echo ""
fi

echo -e "${GREEN}Verification:${NC}"
echo -e "  # Test health endpoint"
echo -e "  curl $SERVICE_URL/health"
echo ""
echo -e "  # View API logs"
echo -e "  gcloud run logs read api --region $REGION --limit 50"
echo ""
echo -e "  # View worker logs"
echo -e "  kubectl logs -n temporal-workers -l worker-type=general -f"
echo ""

echo -e "${GREEN}Next steps:${NC}"
echo -e "  1. Update frontend .env: VITE_API_URL=$SERVICE_URL"
echo -e "  2. Test topic endpoints: $SERVICE_URL/api/v1/topics"
echo -e "  3. Monitor logs for any errors"
echo ""

echo -e "${YELLOW}Documentation:${NC}"
echo -e "  • API Migration Guide: API_MIGRATION_GUIDE.md"
echo -e "  • Verification Results: API_VERIFICATION_RESULTS.md"
echo ""

echo -e "${GREEN}Deployment successful! ✅${NC}"

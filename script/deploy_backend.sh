#!/bin/bash
# Deploy FastAPI backend to Cloud Run

set -e

echo "🚀 Deploying Backend API to Cloud Run"
echo "======================================"
echo ""

# Check if gcloud is configured
if ! gcloud config get-value project &>/dev/null; then
    echo "❌ Error: No GCP project configured"
    echo "   Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

PROJECT_ID=$(gcloud config get-value project)
REGION=${REGION:-europe-west3}
SERVICE_NAME=${SERVICE_NAME:-hey-sh-backend}
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "📦 Project: $PROJECT_ID"
echo "🌍 Region: $REGION"
echo "🏷️  Service: $SERVICE_NAME"
echo "🖼️  Image: $IMAGE_NAME"
echo ""

# Build Docker image
echo "🔨 Building Docker image..."
echo ""
gcloud builds submit \
    --config cloudbuild_backend.yaml \
    --project "$PROJECT_ID"

echo ""
echo "📦 Deploying to Cloud Run..."
echo ""

# Deploy to Cloud Run
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_NAME" \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --min-instances 0 \
    --max-instances 10 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 60 \
    --set-env-vars "TEMPORAL_TASK_QUEUE=hey-sh-workflows,NEO4J_DATABASE=neo4j" \
    --set-secrets "TEMPORAL_API_KEY=temporal-api-key:latest,TEMPORAL_NAMESPACE=temporal-namespace:latest,TEMPORAL_ADDRESS=temporal-address:latest,NEO4J_URI=neo4j-uri:latest,NEO4J_USER=neo4j-user:latest,NEO4J_PASSWORD=neo4j-password:latest,WEAVIATE_URL=weaviate-url:latest,WEAVIATE_API_KEY=weaviate-api-key:latest,WEAVIATE_GRPC_HOST=weaviate-grpc-host:latest,OPENAI_API_KEY=openai-api-key:latest,SUPABASE_URL=supabase-url:latest,SUPABASE_KEY=supabase-key:latest"

echo ""
echo "✅ Backend deployed successfully!"
echo ""

# Get the service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format "value(status.url)")

echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "🧪 Test health endpoint:"
echo "   curl $SERVICE_URL/health"
echo ""
echo "🔍 View logs:"
echo "   gcloud run logs read $SERVICE_NAME --region $REGION --limit 50"
echo ""
echo "📊 Service details:"
echo "   gcloud run services describe $SERVICE_NAME --region $REGION"
echo ""
echo "🌐 Cloud Console:"
echo "   https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME"
echo ""
echo "⚠️  Update your frontend .env with:"
echo "   VITE_API_URL=$SERVICE_URL"
echo ""

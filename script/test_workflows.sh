#!/bin/bash
# Test script for hey.sh backend workflows
# Usage: ./script/test_workflows.sh

set -e

API_URL="${API_URL:-http://localhost:8001}"
DOMAIN_ID="${DOMAIN_ID:-test-domain-123}"
USER_ID="${USER_ID:-test-user-456}"

echo "🧪 Testing Hey.sh Backend Workflows"
echo "API URL: $API_URL"
echo ""

# Test health endpoint
echo "1️⃣  Testing health endpoint..."
curl -s "$API_URL/health" | jq .
echo ""

# Test document upload workflow
echo "2️⃣  Testing document processing workflow..."
DOC_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/documents" \
  -H "Content-Type: application/json" \
  -d "{
    \"document_id\": \"doc-$(date +%s)\",
    \"domain_id\": \"$DOMAIN_ID\",
    \"file_path\": \"test/sample.pdf\"
  }")

echo "$DOC_RESPONSE" | jq .
DOC_WORKFLOW_ID=$(echo "$DOC_RESPONSE" | jq -r .workflow_id)
echo "Workflow ID: $DOC_WORKFLOW_ID"
echo ""

# Wait a moment
sleep 2

# Check workflow status
echo "3️⃣  Checking workflow status..."
curl -s "$API_URL/api/v1/workflows/$DOC_WORKFLOW_ID" | jq .
echo ""

# Test question answering workflow
echo "4️⃣  Testing question answering workflow..."
QUESTION_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/questions" \
  -H "Content-Type: application/json" \
  -d "{
    \"question_id\": \"q-$(date +%s)\",
    \"question\": \"What are the main topics in our domain?\",
    \"domain_id\": \"$DOMAIN_ID\",
    \"user_id\": \"$USER_ID\"
  }")

echo "$QUESTION_RESPONSE" | jq .
QUESTION_WORKFLOW_ID=$(echo "$QUESTION_RESPONSE" | jq -r .workflow_id)
echo "Workflow ID: $QUESTION_WORKFLOW_ID"
echo ""

# Test review workflow
echo "5️⃣  Testing quality review workflow..."
REVIEW_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/reviews" \
  -H "Content-Type: application/json" \
  -d "{
    \"review_id\": \"review-$(date +%s)\",
    \"reviewable_type\": \"answer\",
    \"reviewable_id\": \"$QUESTION_WORKFLOW_ID\",
    \"domain_id\": \"$DOMAIN_ID\"
  }")

echo "$REVIEW_RESPONSE" | jq .
echo ""

echo "✅ All workflow tests completed!"
echo ""
echo "View workflows in Temporal UI: http://localhost:8090"

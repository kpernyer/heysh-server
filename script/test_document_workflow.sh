#!/bin/bash
# Test document processing workflow with Temporal
# This script demonstrates the complete document processing pipeline:
# 1. Create a test document
# 2. Trigger DocumentProcessing workflow via API
# 3. Monitor workflow execution
# 4. Verify results in Weaviate and Neo4j

set -e

API_URL="${API_URL:-http://localhost:8001}"
DOMAIN_ID="${DOMAIN_ID:-ml-research-$(date +%s)}"
USER_ID="${USER_ID:-test-user-123}"

echo "🧪 Testing Document Processing with Temporal Workflow"
echo "=========================================="
echo "API URL: $API_URL"
echo "Domain ID: $DOMAIN_ID"
echo "User ID: $USER_ID"
echo ""

# Test 1: Create a test document (simulate upload)
echo "1️⃣  Creating test document file..."
TEST_DOC_PATH="/tmp/test-ml-paper.txt"
cat > "$TEST_DOC_PATH" << 'EOF'
Machine Learning Best Practices for Production Systems

Abstract:
This paper discusses best practices for deploying machine learning models in production environments. We cover topics including model versioning, A/B testing, monitoring, and continuous training.

Introduction:
Machine learning systems in production face unique challenges compared to research environments. Model drift, data quality issues, and scalability concerns must be addressed systematically.

Key Recommendations:
1. Implement comprehensive monitoring for model performance degradation
2. Use feature stores for consistent feature engineering
3. Automate retraining pipelines with clear trigger conditions
4. Maintain model versioning and rollback capabilities
5. Monitor data drift and distribution shifts

Conclusion:
Production ML systems require careful engineering practices beyond model accuracy. Organizations must invest in infrastructure, monitoring, and processes to ensure reliable ML deployments.
EOF

echo "✅ Created test document: $TEST_DOC_PATH"
echo ""

# Test 2: Create domain for document
echo "2️⃣  Creating domain for document..."
curl -s -X POST "$API_URL/api/v1/domains" \
  -H "Content-Type: application/json" \
  -d "{
    \"domain_id\": \"$DOMAIN_ID\",
    \"name\": \"ML Production Systems\",
    \"description\": \"Best practices and guidelines for deploying machine learning models to production\",
    \"created_by\": \"$USER_ID\"
  }" | jq .

sleep 2
echo ""

# Test 3: Trigger document processing workflow
echo "3️⃣  Triggering document processing workflow..."
DOC_ID="doc-$(date +%s)"
WORKFLOW_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/documents" \
  -H "Content-Type: application/json" \
  -d "{
    \"document_id\": \"$DOC_ID\",
    \"domain_id\": \"$DOMAIN_ID\",
    \"file_path\": \"test/ml-production-best-practices.pdf\"
  }")

echo "$WORKFLOW_RESPONSE" | jq .
WORKFLOW_ID=$(echo "$WORKFLOW_RESPONSE" | jq -r .workflow_id)
echo ""
echo "📋 Workflow ID: $WORKFLOW_ID"
echo ""

# Test 4: Monitor workflow status
echo "4️⃣  Monitoring workflow status..."
for i in {1..5}; do
  echo "   Check $i/5..."
  STATUS_RESPONSE=$(curl -s "$API_URL/api/v1/workflows/$WORKFLOW_ID")
  echo "$STATUS_RESPONSE" | jq .

  STATUS=$(echo "$STATUS_RESPONSE" | jq -r .status)

  if [ "$STATUS" = "COMPLETED" ]; then
    echo "✅ Workflow completed successfully!"
    break
  elif [ "$STATUS" = "FAILED" ]; then
    echo "❌ Workflow failed!"
    break
  else
    echo "   Status: $STATUS - waiting..."
    sleep 3
  fi
done
echo ""

# Test 5: Search for document in Weaviate (semantic search)
echo "5️⃣  Searching for document using semantic search..."
echo "   Query: 'model monitoring and drift detection'"
curl -s "$API_URL/api/v1/domains/search?q=model%20monitoring%20and%20drift%20detection&user_id=$USER_ID&use_llm=true" | jq '.results.vector_results[0] // "No results found"'
echo ""

# Test 6: Search for production best practices
echo "6️⃣  Searching for 'production ML best practices'..."
curl -s "$API_URL/api/v1/domains/search?q=production%20ML%20best%20practices&user_id=$USER_ID&use_llm=true" | jq '.results.vector_results[0] // "No results found"'
echo ""

# Test 7: Check LLM summary
echo "7️⃣  Getting LLM summary for search results..."
SUMMARY_RESPONSE=$(curl -s "$API_URL/api/v1/domains/search?q=machine%20learning%20deployment&user_id=$USER_ID&use_llm=true")
echo "$SUMMARY_RESPONSE" | jq -r '.summary // "No summary available"'
echo ""

# Summary
echo "=========================================="
echo "✅ Document Workflow Test Complete!"
echo ""
echo "📊 Test Summary:"
echo "   - Document ID: $DOC_ID"
echo "   - Domain ID: $DOMAIN_ID"
echo "   - Workflow ID: $WORKFLOW_ID"
echo ""
echo "🔍 Next Steps:"
echo "   1. View workflow in Temporal UI: http://localhost:8090"
echo "   2. Query Weaviate directly for indexed vectors"
echo "   3. Query Neo4j for graph relationships"
echo ""
echo "🌐 Temporal UI: http://localhost:8090"
echo "🔗 Neo4j Browser: http://localhost:7474"
echo ""

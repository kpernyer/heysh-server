#!/bin/bash
# Test domain creation and semantic search
# Usage: ./script/test_domain_search.sh

set -e

API_URL="${API_URL:-http://localhost:8001}"
USER_ID="${USER_ID:-test-user-123}"

echo "🧪 Testing Domain Creation and Semantic Search"
echo "API URL: $API_URL"
echo "User ID: $USER_ID"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check API health
echo -e "${BLUE}0️⃣  Checking API health...${NC}"
curl -s "$API_URL/health" | jq .
echo ""

# Test 1: Create first domain
echo -e "${GREEN}1️⃣  Creating first domain: 'Machine Learning Research'${NC}"
DOMAIN1_ID="ml-research-$(date +%s)"
curl -s -X POST "$API_URL/api/v1/domains" \
  -H "Content-Type: application/json" \
  -d "{
    \"domain_id\": \"$DOMAIN1_ID\",
    \"name\": \"Machine Learning Research\",
    \"description\": \"A collaborative space for researchers working on deep learning, neural networks, and computer vision. We share papers, discuss breakthroughs in artificial intelligence, and coordinate on ML projects.\",
    \"created_by\": \"$USER_ID\"
  }" | jq .

echo ""
sleep 2

# Test 2: Create second domain with some overlap
echo -e "${GREEN}2️⃣  Creating second domain: 'AI Ethics and Safety'${NC}"
DOMAIN2_ID="ai-ethics-$(date +%s)"
curl -s -X POST "$API_URL/api/v1/domains" \
  -H "Content-Type: application/json" \
  -d "{
    \"domain_id\": \"$DOMAIN2_ID\",
    \"name\": \"AI Ethics and Safety\",
    \"description\": \"Discussing responsible artificial intelligence development, AI safety research, bias in machine learning systems, and ethical implications of AI deployment in society.\",
    \"created_by\": \"$USER_ID\"
  }" | jq .

echo ""
sleep 2

# Test 3: Search for something only in description (low score expected for title match)
echo -e "${YELLOW}3️⃣  Search test: 'computer vision' (only in first domain's description)${NC}"
echo "Expected: Should find ML Research domain with good semantic match"
echo ""
curl -s "$API_URL/api/v1/domains/search?q=computer%20vision&user_id=$USER_ID&use_llm=true" | jq '{
  query: .query,
  result_count: .result_count,
  summary: .summary,
  vector_results: .results.vector_results | map({name, description}),
  graph_results: .results.graph_results | map({name, description})
}'

echo ""
echo "---"
sleep 2

# Test 4: Search for something in both descriptions
echo -e "${YELLOW}4️⃣  Search test: 'artificial intelligence' (in both descriptions)${NC}"
echo "Expected: Should find both domains with good matches"
echo ""
curl -s "$API_URL/api/v1/domains/search?q=artificial%20intelligence&user_id=$USER_ID&use_llm=true" | jq '{
  query: .query,
  result_count: .result_count,
  summary: .summary,
  vector_results: .results.vector_results | map({name, description}),
  graph_results: .results.graph_results | map({name, description})
}'

echo ""
echo "---"
sleep 2

# Test 5: Search for something in one title
echo -e "${YELLOW}5️⃣  Search test: 'ethics' (in second domain's title)${NC}"
echo "Expected: Should strongly match AI Ethics domain"
echo ""
curl -s "$API_URL/api/v1/domains/search?q=ethics&user_id=$USER_ID&use_llm=true" | jq '{
  query: .query,
  result_count: .result_count,
  summary: .summary,
  vector_results: .results.vector_results | map({name, description}),
  graph_results: .results.graph_results | map({name, description})
}'

echo ""
echo "---"
sleep 2

# Test 6: Search for something with semantic similarity (not exact match)
echo -e "${YELLOW}6️⃣  Search test: 'deep neural nets' (semantic match for 'deep learning, neural networks')${NC}"
echo "Expected: Should find ML Research domain via semantic similarity"
echo ""
curl -s "$API_URL/api/v1/domains/search?q=deep%20neural%20nets&user_id=$USER_ID&use_llm=true" | jq '{
  query: .query,
  result_count: .result_count,
  summary: .summary,
  vector_results: .results.vector_results | map({name, description}),
  graph_results: .results.graph_results | map({name, description})
}'

echo ""
echo ""
echo -e "${GREEN}✅ All tests completed!${NC}"
echo ""
echo "📝 Summary:"
echo "   - Created 2 domains: $DOMAIN1_ID, $DOMAIN2_ID"
echo "   - Ran 4 search tests demonstrating:"
echo "     • Description-only matches (computer vision)"
echo "     • Cross-domain matches (artificial intelligence)"
echo "     • Title matches (ethics)"
echo "     • Semantic similarity (deep neural nets → deep learning)"
echo ""
echo "💡 View domains in Neo4j: http://localhost:7474"
echo "   Run: MATCH (d:Domain) RETURN d"

#!/bin/bash

# Test runner script for local and CI/CD environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
TEST_ENV="${TEST_ENV:-local}"
CLEANUP="${CLEANUP:-true}"
VERBOSE="${VERBOSE:-false}"

echo -e "${GREEN}🧪 Starting Document Workflow Tests${NC}"
echo "Environment: $TEST_ENV"

# Function to cleanup
cleanup() {
    if [ "$CLEANUP" == "true" ]; then
        echo -e "${YELLOW}🧹 Cleaning up test environment...${NC}"
        docker-compose -f docker-compose.test.yml down -v
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# 1. Start test environment
echo -e "${GREEN}📦 Starting test infrastructure...${NC}"
docker-compose -f docker-compose.test.yml up -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"

# Wait for Temporal
until docker-compose -f docker-compose.test.yml exec -T temporal \
    temporal workflow list --namespace default &>/dev/null; do
    echo -n "."
    sleep 2
done
echo -e "\n${GREEN}✅ Temporal is ready${NC}"

# Wait for Mock AI
until curl -f http://localhost:8001/health &>/dev/null; do
    echo -n "."
    sleep 1
done
echo -e "\n${GREEN}✅ Mock AI service is ready${NC}"

# Wait for databases
until docker-compose -f docker-compose.test.yml exec -T neo4j \
    cypher-shell -u neo4j -p testpassword "MATCH (n) RETURN count(n)" &>/dev/null; do
    echo -n "."
    sleep 2
done
echo -e "\n${GREEN}✅ Neo4j is ready${NC}"

# 2. Run unit tests
echo -e "${GREEN}🔬 Running unit tests...${NC}"
python -m pytest test/unit/ -v --tb=short || true

# 3. Run integration tests
echo -e "${GREEN}🔗 Running integration tests...${NC}"
python -m pytest test/test_workflows.py -v --tb=short

# 4. Run end-to-end tests
echo -e "${GREEN}🚀 Running end-to-end tests...${NC}"
python -m pytest test/test_workflows.py::test_end_to_end_document_flow -v

# 5. Run load tests (optional)
if [ "$RUN_LOAD_TESTS" == "true" ]; then
    echo -e "${GREEN}⚡ Running load tests...${NC}"
    python test/load_test.py
fi

# 6. Generate test report
echo -e "${GREEN}📊 Generating test report...${NC}"
python -m pytest test/ \
    --html=test-results/report.html \
    --self-contained-html \
    --cov=workflow \
    --cov=activity \
    --cov-report=html:test-results/coverage

echo -e "${GREEN}✅ All tests completed!${NC}"
echo "Test report: test-results/report.html"
echo "Coverage report: test-results/coverage/index.html"

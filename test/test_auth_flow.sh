#!/bin/bash
# Test script for API authentication flow
# Tests the complete auth flow: invite validation → signup → login → protected endpoint

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

API_URL="${API_URL:-http://localhost:8000}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Hey.sh Auth Flow Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Test 1: Validate Invite Code
echo -e "${BLUE}1️⃣  Testing: Validate Invite Code${NC}"
echo "Endpoint: POST /auth/validate-invite"
echo "Code: TEST-1234"
echo ""

INVITE_RESPONSE=$(curl -s -X POST "$API_URL/auth/validate-invite" \
  -H "Content-Type: application/json" \
  -d '{"code":"TEST-1234"}')

echo "Response: $INVITE_RESPONSE"

# Check if valid (for now, we expect it to fail since no real invite exists)
if echo "$INVITE_RESPONSE" | grep -q '"valid"'; then
  echo -e "${GREEN}✓ Endpoint working${NC}"
else
  echo -e "${RED}✗ No 'valid' field in response${NC}"
fi

echo ""

# Test 2: Health Check
echo -e "${BLUE}2️⃣  Testing: Health Check${NC}"
echo "Endpoint: GET /health"
echo ""

HEALTH=$(curl -s -X GET "$API_URL/health")
echo "Response: $HEALTH"

if echo "$HEALTH" | grep -q "healthy"; then
  echo -e "${GREEN}✓ Server is healthy${NC}"
else
  echo -e "${RED}✗ Server health check failed${NC}"
fi

echo ""

# Test 3: Root Endpoint
echo -e "${BLUE}3️⃣  Testing: Root Endpoint${NC}"
echo "Endpoint: GET /"
echo ""

ROOT=$(curl -s -X GET "$API_URL/")
echo "Response: $ROOT"

if echo "$ROOT" | grep -q "Hey.sh Backend API"; then
  echo -e "${GREEN}✓ API is running${NC}"
else
  echo -e "${RED}✗ API root endpoint failed${NC}"
fi

echo ""

# Test 4: Protected Endpoint Without Token
echo -e "${BLUE}4️⃣  Testing: Protected Endpoint Without Token (Should Fail)${NC}"
echo "Endpoint: GET /api/v1/documents"
echo ""

UNAUTH=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X GET "$API_URL/api/v1/documents")
HTTP_CODE=$(echo "$UNAUTH" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$UNAUTH" | sed '/^HTTP_STATUS:/d')

echo "Response: $BODY"
echo "Status: $HTTP_CODE"

if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
  echo -e "${GREEN}✓ Correctly rejected request without token${NC}"
else
  echo -e "${RED}✗ Should have returned 401/403, got $HTTP_CODE${NC}"
fi

echo ""

# Test 5: Create Test Invite Code (if you have a way to do this)
echo -e "${BLUE}5️⃣  Creating Test Invite Code${NC}"
echo "Note: This requires backend database access or admin endpoint"
echo "For now, using default test invite code"
echo ""

INVITE_CODE="TEST-12345678"
echo -e "${GREEN}✓ Using invite code: $INVITE_CODE${NC}"

echo ""

# Test 6: Register New User
echo -e "${BLUE}6️⃣  Testing: User Registration${NC}"
echo "Endpoint: POST /auth/register"

# Generate unique email
TIMESTAMP=$(date +%s)
TEST_EMAIL="test-${TIMESTAMP}@example.com"
TEST_PASSWORD="TestPassword123"

echo "Email: $TEST_EMAIL"
echo "Password: $TEST_PASSWORD"
echo "Invite Code: $INVITE_CODE"
echo ""

REGISTER_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"invite_code\":\"$INVITE_CODE\"}")

HTTP_CODE=$(echo "$REGISTER_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$REGISTER_RESPONSE" | sed '/^HTTP_STATUS:/d')

echo "Response: $BODY"
echo "Status: $HTTP_CODE"

# Extract token if successful
if [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "200" ]; then
  ACCESS_TOKEN=$(echo "$BODY" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
  USER_ID=$(echo "$BODY" | grep -o '"user_id":"[^"]*' | cut -d'"' -f4)

  if [ -n "$ACCESS_TOKEN" ]; then
    echo -e "${GREEN}✓ Registration successful${NC}"
    echo "Token: ${ACCESS_TOKEN:0:20}..."
    echo "User ID: $USER_ID"
  fi
else
  echo -e "${RED}✗ Registration failed${NC}"
  ACCESS_TOKEN=""
fi

echo ""

# Test 7: Get User Profile (if registration succeeded)
if [ -n "$ACCESS_TOKEN" ]; then
  echo -e "${BLUE}7️⃣  Testing: Get User Profile${NC}"
  echo "Endpoint: GET /auth/me"
  echo "Token: ${ACCESS_TOKEN:0:20}..."
  echo ""

  PROFILE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X GET "$API_URL/auth/me" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

  HTTP_CODE=$(echo "$PROFILE" | grep "HTTP_STATUS" | cut -d: -f2)
  BODY=$(echo "$PROFILE" | sed '/^HTTP_STATUS:/d')

  echo "Response: $BODY"
  echo "Status: $HTTP_CODE"

  if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Successfully retrieved user profile${NC}"
  else
    echo -e "${RED}✗ Failed to get profile${NC}"
  fi

  echo ""

  # Test 8: List Documents (Protected Endpoint)
  echo -e "${BLUE}8️⃣  Testing: Protected Endpoint with Token${NC}"
  echo "Endpoint: GET /api/v1/documents"
  echo ""

  DOCS=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X GET "$API_URL/api/v1/documents" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

  HTTP_CODE=$(echo "$DOCS" | grep "HTTP_STATUS" | cut -d: -f2)
  BODY=$(echo "$DOCS" | sed '/^HTTP_STATUS:/d')

  echo "Response: $BODY"
  echo "Status: $HTTP_CODE"

  if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Successfully accessed protected endpoint${NC}"
  else
    echo -e "${RED}✗ Failed to access protected endpoint${NC}"
  fi

  echo ""

  # Test 9: Logout
  echo -e "${BLUE}9️⃣  Testing: Logout${NC}"
  echo "Endpoint: POST /auth/logout"
  echo ""

  LOGOUT=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$API_URL/auth/logout" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

  HTTP_CODE=$(echo "$LOGOUT" | grep "HTTP_STATUS" | cut -d: -f2)
  BODY=$(echo "$LOGOUT" | sed '/^HTTP_STATUS:/d')

  echo "Response: $BODY"
  echo "Status: $HTTP_CODE"

  if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Logout successful${NC}"
  else
    echo -e "${RED}✗ Logout failed${NC}"
  fi

else
  echo -e "${RED}Skipping remaining tests (registration failed)${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Auth Flow Test Complete${NC}"
echo -e "${BLUE}========================================${NC}"

#!/bin/bash
# Test script for FastAPI server
# Usage: bash test_fastapi.sh

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="http://localhost:8000"

echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  FastAPI Server Test Script${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""

# Check if server is running
echo -e "${BLUE}Checking if server is running...${NC}"
if ! curl -s "${API_URL}/" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Server not running. Start it with:${NC}"
    echo -e "${YELLOW}   uvicorn examples.fastapi_server:app --reload${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Server is running${NC}"
echo ""

# Health check
echo -e "${BLUE}1. Health Check${NC}"
echo "GET /"
curl -s "${API_URL}/" | python -m json.tool
echo ""
echo ""

# Test cases
declare -a requests=(
    "My invoice has extra charges"
    "I can't log into my account"
    "How much does the enterprise plan cost?"
    "My credit card was charged twice"
    "The software keeps crashing when I open files"
    "Do you offer volume discounts?"
)

for i in "${!requests[@]}"; do
    num=$((i + 1))
    request="${requests[$i]}"

    echo -e "${BLUE}$num. Testing Request${NC}"
    echo "Request: \"$request\""

    response=$(curl -s -X POST "${API_URL}/route" \
        -H "Content-Type: application/json" \
        -d "{\"request\": \"$request\"}")

    echo "$response" | python -m json.tool

    # Extract route for summary
    route=$(echo "$response" | python -c "import sys, json; print(json.load(sys.stdin)['route'])" 2>/dev/null || echo "unknown")
    echo -e "${GREEN}→ Routed to: $route${NC}"
    echo ""
    sleep 1  # Small delay to make output readable
done

echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Test Complete!${NC}"
echo -e "${GREEN}  Check Langfuse dashboard for traces${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"

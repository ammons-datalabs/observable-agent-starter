#!/bin/bash
# Demo script for Observable Agent Starter screencast
# Run this with: bash demo.sh

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print with delay (looks better in recordings)
print_command() {
    echo -e "${BLUE}$ $1${NC}"
    sleep 0.5
}

# Function to add pause between sections
pause() {
    sleep 2
}

clear
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Observable Agent Starter - Demo${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
sleep 2

# Demo 1: Basic CLI usage
echo -e "${YELLOW}→ Demo 1: CLI Agent with Fallback Policy${NC}"
echo ""
sleep 1

print_command "python -m agents.example"
python -m agents.example
pause

# Demo 2: CLI with different inputs
echo ""
echo -e "${YELLOW}→ Demo 2: Testing Different Routing Scenarios${NC}"
echo ""
sleep 1

# Create a temporary Python script for multiple examples
cat > /tmp/demo_examples.py << 'PYTHON'
from agents.example.agent import ExampleAgent

agent = ExampleAgent()

examples = [
    "I can't log into my account",
    "How much does the premium plan cost?",
    "My credit card was charged twice",
]

for i, request in enumerate(examples, 1):
    print(f"\n[Example {i}]")
    print(f"Request: {request}")
    result = agent(request=request)
    print(f"Route: {result['route']}")
    print(f"Explanation: {result['explanation'][:80]}...")
PYTHON

print_command "python /tmp/demo_examples.py"
python /tmp/demo_examples.py
pause

# Demo 3: FastAPI server (in background)
echo ""
echo -e "${YELLOW}→ Demo 3: Production FastAPI Server${NC}"
echo ""
sleep 1

print_command "uvicorn examples.fastapi_server:app &"
uvicorn examples.fastapi_server:app --port 8000 > /tmp/uvicorn.log 2>&1 &
UVICORN_PID=$!
sleep 3

print_command "curl -X POST http://localhost:8000/route -H 'Content-Type: application/json' -d '{\"request\": \"My invoice has extra charges\"}' | jq"
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"request": "My invoice has extra charges"}' \
  2>/dev/null | python -m json.tool

pause

print_command "curl -X POST http://localhost:8000/route -H 'Content-Type: application/json' -d '{\"request\": \"I need help resetting my password\"}' | jq"
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"request": "I need help resetting my password"}' \
  2>/dev/null | python -m json.tool

# Cleanup
kill $UVICORN_PID 2>/dev/null || true
rm -f /tmp/demo_examples.py

pause
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Demo Complete!${NC}"
echo -e "${GREEN}  → Observability built-in with Langfuse${NC}"
echo -e "${GREEN}  → Production-ready with FastAPI${NC}"
echo -e "${GREEN}  → CI/CD ready with GitHub Actions${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""

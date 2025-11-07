#!/bin/bash
# Socrates CLI Test Runner
# Runs unit tests and integration tests for the CLI

set -e  # Exit on error

echo "═══════════════════════════════════════════════════"
echo "   Socrates CLI Test Suite"
echo "═══════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo -e "${RED}✗ Python not found${NC}"
    exit 1
fi

# Check if required packages are installed
echo -e "${YELLOW}Checking dependencies...${NC}"
python -c "import requests, rich, prompt_toolkit" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Missing dependencies${NC}"
    echo "  Install with: pip install -r cli-requirements.txt"
    exit 1
fi
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Run unit tests
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Running Unit Tests (no backend required)${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
echo ""

python test_cli.py
UNIT_TEST_RESULT=$?

if [ $UNIT_TEST_RESULT -eq 0 ]; then
    echo -e "\n${GREEN}✓ Unit tests passed${NC}\n"
else
    echo -e "\n${RED}✗ Unit tests failed${NC}\n"
    echo "Would you like to continue with integration tests? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if backend is running
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Checking backend connection...${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
echo ""

BACKEND_URL="${SOCRATES_API_URL:-http://localhost:8000}"
echo "Testing connection to: $BACKEND_URL"

# Try to connect to backend
if curl -s -f -o /dev/null --max-time 5 "$BACKEND_URL/docs"; then
    echo -e "${GREEN}✓ Backend is running${NC}\n"

    # Run integration tests
    echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}Running Integration Tests (requires backend)${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
    echo ""

    python test_cli_integration.py --api-url "$BACKEND_URL"
    INTEGRATION_TEST_RESULT=$?

    if [ $INTEGRATION_TEST_RESULT -eq 0 ]; then
        echo -e "\n${GREEN}✓ Integration tests passed${NC}"
    else
        echo -e "\n${RED}✗ Integration tests failed${NC}"
    fi
else
    echo -e "${RED}✗ Backend not running at $BACKEND_URL${NC}"
    echo ""
    echo -e "${YELLOW}Integration tests skipped.${NC}"
    echo ""
    echo "To run integration tests, start the backend:"
    echo "  cd backend"
    echo "  uvicorn app.main:app --reload"
    echo ""
    INTEGRATION_TEST_RESULT=0  # Don't fail if backend isn't running
fi

# Summary
echo ""
echo "═══════════════════════════════════════════════════"
echo "   Test Results Summary"
echo "═══════════════════════════════════════════════════"

if [ $UNIT_TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ Unit Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Unit Tests: FAILED${NC}"
fi

if curl -s -f -o /dev/null --max-time 5 "$BACKEND_URL/docs" 2>/dev/null; then
    if [ $INTEGRATION_TEST_RESULT -eq 0 ]; then
        echo -e "${GREEN}✓ Integration Tests: PASSED${NC}"
    else
        echo -e "${RED}✗ Integration Tests: FAILED${NC}"
    fi
else
    echo -e "${YELLOW}⊘ Integration Tests: SKIPPED (backend not running)${NC}"
fi

echo "═══════════════════════════════════════════════════"
echo ""

# Exit with error if either test suite failed
if [ $UNIT_TEST_RESULT -ne 0 ] || [ $INTEGRATION_TEST_RESULT -ne 0 ]; then
    exit 1
fi

exit 0

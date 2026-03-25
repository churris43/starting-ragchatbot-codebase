#!/bin/bash
# Frontend Code Quality Script
# Run this script to check and fix code quality issues

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "  Frontend Code Quality Checks"
echo "========================================"
echo ""

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    npm install
    echo ""
fi

# Parse arguments
FIX_MODE=false
CHECK_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX_MODE=true
            shift
            ;;
        --check)
            CHECK_ONLY=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./quality.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --check    Only check for issues (no fixes)"
            echo "  --fix      Automatically fix issues"
            echo "  --help     Show this help message"
            echo ""
            echo "Default: Runs checks without automatic fixes"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

if [ "$FIX_MODE" = true ]; then
    echo -e "${YELLOW}Running in FIX mode - will automatically fix issues${NC}"
    echo ""

    echo "1. Formatting code with Prettier..."
    npm run format
    echo -e "${GREEN}   Done!${NC}"
    echo ""

    echo "2. Fixing ESLint issues..."
    npm run lint:fix
    echo -e "${GREEN}   Done!${NC}"
    echo ""

    echo -e "${GREEN}========================================"
    echo "  All fixes applied successfully!"
    echo "========================================${NC}"
else
    echo "Running quality checks..."
    echo ""

    FAILED=false

    echo "1. Checking code formatting (Prettier)..."
    if npm run format:check; then
        echo -e "${GREEN}   All files are properly formatted!${NC}"
    else
        echo -e "${RED}   Some files need formatting. Run './quality.sh --fix' to fix.${NC}"
        FAILED=true
    fi
    echo ""

    echo "2. Checking code quality (ESLint)..."
    if npm run lint; then
        echo -e "${GREEN}   No linting issues found!${NC}"
    else
        echo -e "${RED}   Linting issues found. Run './quality.sh --fix' to auto-fix.${NC}"
        FAILED=true
    fi
    echo ""

    if [ "$FAILED" = true ]; then
        echo -e "${RED}========================================"
        echo "  Some checks failed!"
        echo "  Run './quality.sh --fix' to auto-fix"
        echo "========================================${NC}"
        exit 1
    else
        echo -e "${GREEN}========================================"
        echo "  All quality checks passed!"
        echo "========================================${NC}"
    fi
fi

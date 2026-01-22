#!/bin/bash
# =============================================================================
# Deployment Verification Script
# =============================================================================
# Verifies that the frontend deployment has correct runtime configuration.
# Run this after deploying to Cloud Run to catch configuration issues early.
#
# Usage:
#   ./scripts/verify-deployment.sh https://voice-lab.heyuai.com.tw
#   ./scripts/verify-deployment.sh https://voice-lab.heyuai.com.tw https://api.voice-lab.heyuai.com.tw
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FRONTEND_URL="${1:-}"
EXPECTED_API_URL="${2:-}"

if [ -z "$FRONTEND_URL" ]; then
    echo -e "${RED}Error: Frontend URL is required${NC}"
    echo "Usage: $0 <frontend-url> [expected-api-url]"
    echo "Example: $0 https://voice-lab.heyuai.com.tw https://api.voice-lab.heyuai.com.tw"
    exit 1
fi

echo "=================================================="
echo "Deployment Verification"
echo "=================================================="
echo "Frontend URL: $FRONTEND_URL"
echo ""

ERRORS=0

# -----------------------------------------------------------------------------
# Test 1: config.js is accessible
# -----------------------------------------------------------------------------
echo "Checking config.js accessibility..."
CONFIG_RESPONSE=$(curl -s -w "\n%{http_code}" "$FRONTEND_URL/config.js" 2>/dev/null)
HTTP_CODE=$(echo "$CONFIG_RESPONSE" | tail -n1)
CONFIG_CONTENT=$(echo "$CONFIG_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓${NC} config.js is accessible (HTTP $HTTP_CODE)"
else
    echo -e "${RED}✗${NC} config.js is not accessible (HTTP $HTTP_CODE)"
    ERRORS=$((ERRORS + 1))
fi

# -----------------------------------------------------------------------------
# Test 2: config.js uses correct variable name
# -----------------------------------------------------------------------------
echo ""
echo "Checking config.js variable naming..."
if echo "$CONFIG_CONTENT" | grep -q "VITE_API_BASE_URL:"; then
    echo -e "${GREEN}✓${NC} Uses VITE_API_BASE_URL (correct)"
else
    echo -e "${RED}✗${NC} Missing VITE_API_BASE_URL"
    ERRORS=$((ERRORS + 1))
fi

if echo "$CONFIG_CONTENT" | grep -q "VITE_API_URL:"; then
    echo -e "${YELLOW}⚠${NC} Contains old VITE_API_URL (should be migrated)"
fi

# -----------------------------------------------------------------------------
# Test 3: API URL contains /api/v1
# -----------------------------------------------------------------------------
echo ""
echo "Checking API URL format..."
API_URL=$(echo "$CONFIG_CONTENT" | grep -o 'VITE_API_BASE_URL: "[^"]*"' | sed 's/VITE_API_BASE_URL: "//;s/"$//')

if [ -n "$API_URL" ]; then
    echo "  API URL: $API_URL"

    if echo "$API_URL" | grep -q "/api/v1"; then
        echo -e "${GREEN}✓${NC} API URL contains /api/v1"
    else
        echo -e "${RED}✗${NC} API URL missing /api/v1 suffix"
        ERRORS=$((ERRORS + 1))
    fi

    # Check for localhost (should not be in production)
    if echo "$API_URL" | grep -q "localhost"; then
        echo -e "${RED}✗${NC} API URL contains 'localhost' - this will fail in production!"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}✓${NC} API URL does not contain localhost"
    fi

    # If expected URL provided, verify it matches
    if [ -n "$EXPECTED_API_URL" ]; then
        EXPECTED_WITH_PATH="$EXPECTED_API_URL"
        if ! echo "$EXPECTED_WITH_PATH" | grep -q "/api/v1"; then
            EXPECTED_WITH_PATH="$EXPECTED_API_URL/api/v1"
        fi

        if [ "$API_URL" = "$EXPECTED_WITH_PATH" ]; then
            echo -e "${GREEN}✓${NC} API URL matches expected: $EXPECTED_WITH_PATH"
        else
            echo -e "${RED}✗${NC} API URL mismatch"
            echo "    Expected: $EXPECTED_WITH_PATH"
            echo "    Actual:   $API_URL"
            ERRORS=$((ERRORS + 1))
        fi
    fi
else
    echo -e "${RED}✗${NC} Could not extract API URL from config"
    ERRORS=$((ERRORS + 1))
fi

# -----------------------------------------------------------------------------
# Test 4: API health check
# -----------------------------------------------------------------------------
if [ -n "$API_URL" ] && ! echo "$API_URL" | grep -q "localhost"; then
    echo ""
    echo "Checking API health..."
    # Remove /api/v1 and add /api/v1/health
    API_HEALTH_URL=$(echo "$API_URL" | sed 's|/api/v1$||')/api/v1/health

    HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_HEALTH_URL" 2>/dev/null || echo -e "\n000")
    HEALTH_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)

    if [ "$HEALTH_CODE" = "200" ]; then
        echo -e "${GREEN}✓${NC} API health check passed (HTTP $HEALTH_CODE)"
    else
        echo -e "${YELLOW}⚠${NC} API health check returned HTTP $HEALTH_CODE"
        echo "  URL: $API_HEALTH_URL"
    fi
fi

# -----------------------------------------------------------------------------
# Test 5: index.html loads config.js
# -----------------------------------------------------------------------------
echo ""
echo "Checking index.html..."
INDEX_CONTENT=$(curl -s "$FRONTEND_URL/" 2>/dev/null)

if echo "$INDEX_CONTENT" | grep -q 'src="/config.js"'; then
    echo -e "${GREEN}✓${NC} index.html includes config.js"
else
    echo -e "${RED}✗${NC} index.html does not include config.js"
    ERRORS=$((ERRORS + 1))
fi

# Check script order (config.js should be before main.tsx)
CONFIG_POS=$(echo "$INDEX_CONTENT" | grep -n 'config.js' | head -1 | cut -d: -f1)
MAIN_POS=$(echo "$INDEX_CONTENT" | grep -n 'main.tsx\|main.js' | head -1 | cut -d: -f1)

if [ -n "$CONFIG_POS" ] && [ -n "$MAIN_POS" ]; then
    if [ "$CONFIG_POS" -lt "$MAIN_POS" ]; then
        echo -e "${GREEN}✓${NC} config.js loads before main script"
    else
        echo -e "${RED}✗${NC} config.js should load before main script"
        ERRORS=$((ERRORS + 1))
    fi
fi

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo ""
echo "=================================================="
echo "Verification Summary"
echo "=================================================="

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}$ERRORS error(s) found${NC}"
    echo ""
    echo "Common fixes:"
    echo "  1. Rebuild and redeploy the frontend Docker image"
    echo "  2. Check Terraform/Cloud Run environment variables"
    echo "  3. Verify docker-entrypoint.sh is being executed"
    exit 1
fi

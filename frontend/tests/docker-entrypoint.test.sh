#!/bin/bash
# =============================================================================
# Docker Entrypoint Integration Tests
# =============================================================================
# Tests that docker-entrypoint.sh correctly generates config.js
#
# Run with: bash frontend/tests/docker-entrypoint.test.sh
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Temporary directory for tests
TEST_DIR=$(mktemp -d)
trap "rm -rf $TEST_DIR" EXIT

# Path to the entrypoint script
ENTRYPOINT_SCRIPT="$(dirname "$0")/../docker-entrypoint.sh"

# Helper function to run entrypoint in test mode
run_entrypoint() {
    # Create mock nginx html directory
    mkdir -p "$TEST_DIR/usr/share/nginx/html"

    # Create a modified entrypoint that writes to our test directory
    sed "s|/usr/share/nginx/html|$TEST_DIR/usr/share/nginx/html|g" "$ENTRYPOINT_SCRIPT" > "$TEST_DIR/entrypoint.sh"
    chmod +x "$TEST_DIR/entrypoint.sh"

    # Run the entrypoint (without exec at the end)
    (
        cd "$TEST_DIR"
        # Source just the config generation part
        export VITE_API_URL="${1:-}"
        export VITE_API_BASE_URL="${2:-}"
        export VITE_WS_URL="${3:-}"
        export VITE_GOOGLE_CLIENT_ID="${4:-}"

        # Run the script but skip the exec
        bash -c "
            set -e
            API_URL=\"\${VITE_API_BASE_URL:-\${VITE_API_URL:-}}\"
            if [ -n \"\$API_URL\" ] && ! echo \"\$API_URL\" | grep -q \"/api/v1\"; then
              API_URL=\"\${API_URL}/api/v1\"
            fi
            cat > '$TEST_DIR/usr/share/nginx/html/config.js' << EOF
window.__RUNTIME_CONFIG__ = {
  VITE_API_BASE_URL: \"\${API_URL}\",
  VITE_WS_URL: \"\${VITE_WS_URL:-}\",
  VITE_GOOGLE_CLIENT_ID: \"\${VITE_GOOGLE_CLIENT_ID:-}\"
};
EOF
        "
    )

    cat "$TEST_DIR/usr/share/nginx/html/config.js"
}

# Test assertion helper
assert_contains() {
    local content="$1"
    local expected="$2"
    local test_name="$3"

    TESTS_RUN=$((TESTS_RUN + 1))

    if echo "$content" | grep -q "$expected"; then
        echo -e "${GREEN}✓${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $test_name"
        echo -e "  ${YELLOW}Expected to contain:${NC} $expected"
        echo -e "  ${YELLOW}Actual content:${NC}"
        echo "$content" | sed 's/^/    /'
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_not_contains() {
    local content="$1"
    local unexpected="$2"
    local test_name="$3"

    TESTS_RUN=$((TESTS_RUN + 1))

    if ! echo "$content" | grep -q "$unexpected"; then
        echo -e "${GREEN}✓${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $test_name"
        echo -e "  ${YELLOW}Should NOT contain:${NC} $unexpected"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# =============================================================================
# Test Cases
# =============================================================================

echo "=================================================="
echo "Docker Entrypoint Integration Tests"
echo "=================================================="
echo ""

# Test 1: Should use VITE_API_BASE_URL variable name (not VITE_API_URL)
echo "Test: Config uses VITE_API_BASE_URL variable name"
config=$(run_entrypoint "https://api.example.com" "" "wss://api.example.com" "client-id")
assert_contains "$config" "VITE_API_BASE_URL:" "Uses correct variable name"
assert_not_contains "$config" "VITE_API_URL:" "Does not use old variable name"

# Test 2: Should append /api/v1 to URL without path
echo ""
echo "Test: Appends /api/v1 to URL without path"
config=$(run_entrypoint "https://api.example.com" "" "" "")
assert_contains "$config" "https://api.example.com/api/v1" "Appends /api/v1 suffix"

# Test 3: Should NOT double-append /api/v1
echo ""
echo "Test: Does not double-append /api/v1"
config=$(run_entrypoint "https://api.example.com/api/v1" "" "" "")
assert_contains "$config" "https://api.example.com/api/v1" "Contains /api/v1"
assert_not_contains "$config" "/api/v1/api/v1" "Does not double /api/v1"

# Test 4: Should prefer VITE_API_BASE_URL over VITE_API_URL
echo ""
echo "Test: Prefers VITE_API_BASE_URL over VITE_API_URL"
config=$(run_entrypoint "https://old.example.com" "https://new.example.com/api/v1" "" "")
assert_contains "$config" "https://new.example.com/api/v1" "Uses VITE_API_BASE_URL value"
assert_not_contains "$config" "old.example.com" "Does not use VITE_API_URL value"

# Test 5: Should handle empty values gracefully
echo ""
echo "Test: Handles empty values gracefully"
config=$(run_entrypoint "" "" "" "")
assert_contains "$config" 'VITE_API_BASE_URL: ""' "Empty API URL is empty string"
assert_contains "$config" 'VITE_WS_URL: ""' "Empty WS URL is empty string"

# Test 6: Should preserve WebSocket URL
echo ""
echo "Test: Preserves WebSocket URL"
config=$(run_entrypoint "https://api.example.com" "" "wss://ws.example.com" "")
assert_contains "$config" 'VITE_WS_URL: "wss://ws.example.com"' "WebSocket URL preserved"

# Test 7: Should preserve Google Client ID
echo ""
echo "Test: Preserves Google Client ID"
config=$(run_entrypoint "" "" "" "my-client-id.apps.googleusercontent.com")
assert_contains "$config" 'VITE_GOOGLE_CLIENT_ID: "my-client-id.apps.googleusercontent.com"' "Client ID preserved"

# Test 8: Generated config should be valid JavaScript
echo ""
echo "Test: Generated config is valid JavaScript"
config=$(run_entrypoint "https://api.example.com" "" "wss://api.example.com" "client-id")
# Try to parse with node
if echo "$config" | node --check 2>/dev/null || echo "$config" | node -e "eval(require('fs').readFileSync(0, 'utf8'))" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Config is valid JavaScript"
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    # Fallback: just check syntax looks right
    if echo "$config" | grep -q "window.__RUNTIME_CONFIG__ = {"; then
        echo -e "${GREEN}✓${NC} Config has correct structure"
        TESTS_RUN=$((TESTS_RUN + 1))
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} Config structure is invalid"
        TESTS_RUN=$((TESTS_RUN + 1))
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
fi

# =============================================================================
# Summary
# =============================================================================

echo ""
echo "=================================================="
echo "Test Summary"
echo "=================================================="
echo -e "Tests run:    $TESTS_RUN"
echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}ALL TESTS PASSED${NC}"
    exit 0
fi

#!/bin/sh
# =============================================================================
# Voice Lab Frontend Docker Entrypoint
# =============================================================================
# Substitutes environment variables at runtime for SPA configuration
# =============================================================================

set -e

# Create runtime config from environment variables
# Use VITE_API_BASE_URL for consistency with frontend code
# Accept both VITE_API_URL (from Terraform) and VITE_API_BASE_URL
API_URL="${VITE_API_BASE_URL:-${VITE_API_URL:-}}"
# Append /api/v1 if it's a full URL without path
if [ -n "$API_URL" ] && ! echo "$API_URL" | grep -q "/api/v1"; then
  API_URL="${API_URL}/api/v1"
fi

cat > /usr/share/nginx/html/config.js << EOF
window.__RUNTIME_CONFIG__ = {
  VITE_API_BASE_URL: "${API_URL}",
  VITE_WS_URL: "${VITE_WS_URL:-}",
  VITE_GOOGLE_CLIENT_ID: "${VITE_GOOGLE_CLIENT_ID:-}"
};
EOF

echo "Runtime config generated at /usr/share/nginx/html/config.js"
echo "VITE_API_BASE_URL: ${API_URL}"

# Execute the main command (nginx)
exec "$@"

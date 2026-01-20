#!/bin/sh
# =============================================================================
# Voice Lab Frontend Docker Entrypoint
# =============================================================================
# Substitutes environment variables at runtime for SPA configuration
# =============================================================================

set -e

# Create runtime config from environment variables
cat > /usr/share/nginx/html/config.js << EOF
window.__RUNTIME_CONFIG__ = {
  VITE_API_URL: "${VITE_API_URL:-}",
  VITE_WS_URL: "${VITE_WS_URL:-}",
  VITE_GOOGLE_CLIENT_ID: "${VITE_GOOGLE_CLIENT_ID:-}"
};
EOF

echo "Runtime config generated at /usr/share/nginx/html/config.js"

# Execute the main command (nginx)
exec "$@"

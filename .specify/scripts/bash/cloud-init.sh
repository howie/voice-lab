#!/bin/bash
# Cloud environment initialization script
# This script runs automatically when a Cloud session starts via SessionStart hook

set -e

# Get the script directory and repo root
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Check if running in Cloud environment
if [ "$CLAUDE_CODE_REMOTE" != "true" ]; then
  # Local environment, no special handling needed
  exit 0
fi

echo "Running in Claude Code Cloud environment"
echo "================================================"

# Show current branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "Current branch: $CURRENT_BRANCH"

# Check for existing feature state
STATE_DIR="$REPO_ROOT/.specify/state"
STATE_FILE="$STATE_DIR/current-feature.json"

if [ -f "$STATE_FILE" ]; then
  echo ""
  echo "Found existing feature state:"
  cat "$STATE_FILE"
  echo ""

  # Extract feature branch name using grep/sed as fallback if jq unavailable
  if command -v jq &>/dev/null; then
    FEATURE_BRANCH=$(jq -r '.branch // empty' "$STATE_FILE" 2>/dev/null)
  else
    # Fallback using grep and sed
    FEATURE_BRANCH=$(grep -o '"branch"[[:space:]]*:[[:space:]]*"[^"]*"' "$STATE_FILE" 2>/dev/null | sed 's/.*"branch"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
  fi

  if [ -n "$FEATURE_BRANCH" ] && [ "$FEATURE_BRANCH" != "$CURRENT_BRANCH" ]; then
    echo "Warning: Feature branch mismatch!"
    echo "   State file branch: $FEATURE_BRANCH"
    echo "   Current branch: $CURRENT_BRANCH"
    echo ""
    echo "To switch to the feature branch, run:"
    echo "   git fetch && git checkout $FEATURE_BRANCH"
  fi
else
  echo "No existing feature state found"
  echo "   Use /speckit.specify to start a new feature"
fi

# Ensure scripts are executable
echo ""
echo "Setting script permissions..."
chmod +x "$REPO_ROOT"/.specify/scripts/bash/*.sh 2>/dev/null || true

echo ""
echo "Cloud environment initialized"
echo "================================================"

exit 0

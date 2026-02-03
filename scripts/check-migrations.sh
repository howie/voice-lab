#!/usr/bin/env bash
# =============================================================================
# Alembic Migration Integrity Check
# =============================================================================
# Validates that:
#   1. No duplicate revision IDs exist
#   2. There is exactly one head (single migration chain)
#
# Usage:
#   scripts/check-migrations.sh
#
# Exit codes:
#   0 - All checks passed
#   1 - Duplicate revision IDs found or multiple heads detected
# =============================================================================

set -euo pipefail

CYAN='\033[36m'
RED='\033[31m'
GREEN='\033[32m'
RESET='\033[0m'

MIGRATIONS_DIR="backend/alembic/versions"
EXIT_CODE=0

echo -e "${CYAN}Checking Alembic migration integrity...${RESET}"

# ─────────────────────────────────────────────────────────────────────────────
# Check 1: Duplicate revision IDs
# ─────────────────────────────────────────────────────────────────────────────
echo -n "  Checking for duplicate revision IDs... "

DUPLICATES=$(grep -rh '^revision:' "$MIGRATIONS_DIR"/*.py 2>/dev/null \
    | sed 's/revision:[[:space:]]*str[[:space:]]*=[[:space:]]*//' \
    | tr -d '"'"'" \
    | tr -d ' ' \
    | sort | uniq -d)

if [ -n "$DUPLICATES" ]; then
    echo -e "${RED}FAILED${RESET}"
    echo -e "${RED}  Duplicate revision IDs found:${RESET}"
    for dup in $DUPLICATES; do
        echo -e "${RED}    - $dup${RESET}"
        grep -rl "revision:.*[\"']${dup}[\"']" "$MIGRATIONS_DIR"/*.py | while read -r f; do
            echo -e "${RED}      in: $(basename "$f")${RESET}"
        done
    done
    EXIT_CODE=1
else
    echo -e "${GREEN}OK${RESET}"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Check 2: Single head
# ─────────────────────────────────────────────────────────────────────────────
echo -n "  Checking for single migration head... "

HEADS_OUTPUT=$(cd backend && python -c "
import os, re

versions_dir = 'alembic/versions'
revisions = {}
children = set()

for f in os.listdir(versions_dir):
    if not f.endswith('.py') or f.startswith('__'):
        continue
    with open(os.path.join(versions_dir, f)) as fh:
        content = fh.read()
    rev_match = re.search(r'revision:\s*(?:str\s*=\s*)?[\"\\']([^\"\\' ]+)[\"\\']', content)
    down_match = re.search(r'down_revision.*?=\s*(.+?)$', content, re.MULTILINE)
    if rev_match:
        rev = rev_match.group(1)
        revisions[rev] = f
    if down_match:
        down_raw = down_match.group(1).strip()
        for m in re.finditer(r'[\"\\']([^\"\\' ]+)[\"\\']', down_raw):
            children.add(m.group(1))

heads = [r for r in revisions if r not in children]
print(len(heads))
for h in heads:
    print(f'{h} ({revisions[h]})')
" 2>&1)

NUM_HEADS=$(echo "$HEADS_OUTPUT" | head -1)

if [ "$NUM_HEADS" -gt 1 ]; then
    echo -e "${RED}FAILED${RESET}"
    echo -e "${RED}  Found $NUM_HEADS heads (expected 1):${RESET}"
    echo "$HEADS_OUTPUT" | tail -n +2 | while read -r line; do
        echo -e "${RED}    - $line${RESET}"
    done
    echo -e "${RED}  Run: cd backend && alembic merge heads -m \"merge branches\"${RESET}"
    EXIT_CODE=1
else
    HEAD_NAME=$(echo "$HEADS_OUTPUT" | tail -1)
    echo -e "${GREEN}OK ($HEAD_NAME)${RESET}"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Result
# ─────────────────────────────────────────────────────────────────────────────
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}All migration checks passed.${RESET}"
else
    echo -e "${RED}Migration checks failed. Fix the issues above before committing.${RESET}"
fi

exit $EXIT_CODE

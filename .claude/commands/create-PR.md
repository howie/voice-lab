# Create Pull Request & Track Usage

This command automates the process of verifying code quality, creating a GitHub Pull Request, and tracking token usage for the feature.

## Prerequisites

- `gh` CLI tool must be installed and authenticated.
- You must be on the feature branch you want to merge.

## Workflow

### Step 1: Verify Code Quality

Run the project's verification suite to ensure everything is green before pushing.

```bash
# Run linting and type checking
make check

# Run all tests
make test
```

**Stop** if any of the above commands fail. Fix the issues first.

### Step 2: Push Branch

Ensure your local branch is up to date and pushed to the remote.

```bash
# Push current branch to origin
git push -u origin HEAD
```

### Step 3: Create Pull Request

Generate a Pull Request using the GitHub CLI. 
The title and body will be interactively prompted or can be auto-generated from commits.

```bash
# Create PR interactively
gh pr create --web
# OR use flags to skip prompts:
# gh pr create --title "feat: Description" --body "Detailed description..."
```

### Step 4: Track Token Usage

Record the estimated token consumption for this feature.

```bash
# Get current branch name as feature identifier
FEATURE_NAME=$(git rev-parse --abbrev-ref HEAD)

# Create tracking file if missing
if [ ! -f .token_usage.csv ]; then
    echo "date,feature,tokens" > .token_usage.csv
fi

# ---------------------------------------------------------
# ACTION REQUIRED: Replace <TOKEN_COUNT> with actual value
# ---------------------------------------------------------
TOKEN_COUNT=0  # <-- UPDATE THIS VALUE

echo "$(date +%F),$FEATURE_NAME,$TOKEN_COUNT" >> .token_usage.csv
echo "Recorded $TOKEN_COUNT tokens for feature '$FEATURE_NAME'"
```

### Step 5: Calculate Consumption

View total tokens consumed for the current feature and overall.

```bash
FEATURE_NAME=$(git rev-parse --abbrev-ref HEAD)

echo "--- Token Usage Report ---"
echo "Feature ($FEATURE_NAME):"
awk -F',' -v feat="$FEATURE_NAME" '$2 == feat {sum+=$3} END {print sum ? sum : 0}' .token_usage.csv

echo "Total Project:"
awk -F',' 'NR>1 {sum+=$3} END {print sum ? sum : 0}' .token_usage.csv
```

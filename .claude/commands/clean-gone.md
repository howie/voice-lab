---
description: Enhanced version - Clean branches marked as [gone] AND optionally all merged branches with PRs
---

## Your Task

Clean up stale local git branches. This command can:
1. Clean branches marked as [gone] (remote deleted)
2. Optionally clean ALL branches with merged PRs

## Commands to Execute

### Step 1: Check [gone] branches

```bash
echo "=== Checking [gone] branches ==="
git branch -v | grep '\[gone\]'
```

### Step 2: Check merged PRs

```bash
echo "=== Checking merged PRs ==="
# Get local branches
local_branches=$(git branch --format='%(refname:short)' | grep -v '^main$')

# Get merged PRs
gh pr list --state merged --json number,headRefName,state --limit 100
```

### Step 3: Ask user preference

Present options:
- `1`: Clean only [gone] branches (safe, remote already deleted)
- `2`: Clean [gone] branches + all merged PR branches (more thorough)
- `3`: Cancel

### Step 4: Execute cleanup based on choice

**Option 1: Clean [gone] branches only**
```bash
git branch -v | grep '\[gone\]' | sed 's/^[+* ]//' | awk '{print $1}' | while read branch; do
  echo "Processing branch: $branch"
  worktree=$(git worktree list | grep "\\[$branch\\]" | awk '{print $1}')
  if [ ! -z "$worktree" ] && [ "$worktree" != "$(git rev-parse --show-toplevel)" ]; then
    echo "  Removing worktree: $worktree"
    git worktree remove --force "$worktree"
  fi
  echo "  Deleting branch: $branch"
  git branch -D "$branch"
done
```

**Option 2: Clean [gone] + merged PR branches**
```bash
# First clean [gone] branches (same as option 1)
# Then clean merged PR branches (same as /clean-merged command)
```

## Expected Behavior

1. Show summary of:
   - Branches marked as [gone]
   - Branches with merged PRs
   - Total branches to be cleaned

2. Ask user for confirmation and cleanup strategy

3. Remove worktrees and delete branches accordingly

4. Provide detailed cleanup report

## Safety Features

- ✅ Always show preview before deletion
- ✅ User confirmation required for option 2
- ✅ Separate handling for [gone] vs merged PR branches
- ✅ Never delete main branch
- ✅ Check worktrees before deletion

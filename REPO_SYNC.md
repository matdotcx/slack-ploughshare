# Slack Ploughshare - Repository Sync Guide

This document explains how to sync code between multiple forks of Slack Ploughshare whilst maintaining separate state data for different Slack workspaces.

## Background

When running Slack Ploughshare in multiple workspaces (e.g., production and testing), you may maintain separate forks that:
- Share the same codebase
- Track separate state files for each workspace

State files include:
- `state/channel_analysis.csv`
- `state/channel_analysis.json`
- `state/channel_warnings.json`

These files are tracked in git (required for GitHub Actions workflows) but should remain separate between forks.

## Why State Files Are Tracked

State files MUST be tracked in git because:
1. GitHub Actions workflows commit state updates after each run
2. This provides persistence across workflow executions
3. State history can be reviewed via git log
4. Each workspace has different Slack data

## Syncing Code Between Forks

When syncing code changes from one fork to another, follow these steps to preserve each repository's state files.

### Option 1: Cherry-Pick Specific Commits (Recommended)

This is the safest method when you have specific commits to sync:

```bash
# In your primary fork clone
git remote add secondary git@github.com:org/slack-ploughshare.git
git fetch secondary

# Cherry-pick specific commits (excluding state file changes)
git cherry-pick <commit-hash>

# If the commit includes state file changes, unstage them:
git reset HEAD state/
git checkout -- state/

# Then push
git push secondary main
```

### Option 2: Push with State File Exclusion

When you want to push all commits but preserve the secondary fork's state:

```bash
# In your primary fork clone
git remote add secondary git@github.com:org/slack-ploughshare.git

# Create a temporary branch with secondary's state files
git fetch secondary main
git checkout -b sync-to-secondary

# Get secondary's state files
git checkout secondary/main -- state/

# Commit the preserved state
git add state/
git commit -m "chore: preserve state during sync"

# Push to secondary
git push secondary sync-to-secondary:main

# Clean up
git checkout main
git branch -D sync-to-secondary
```

### Option 3: Interactive Rebase (For Complex Syncs)

When you need to sync multiple commits whilst carefully managing state:

```bash
# In your primary fork clone
git remote add secondary git@github.com:org/slack-ploughshare.git
git fetch secondary

# Create sync branch
git checkout -b sync-to-secondary secondary/main

# Rebase your changes onto secondary
git rebase main

# During rebase, when conflicts occur in state/ files:
# Always keep secondary's version:
git checkout --theirs state/
git add state/
git rebase --continue

# Push to secondary
git push secondary sync-to-secondary:main --force-with-lease

# Clean up
git checkout main
git branch -D sync-to-secondary
```

## What NOT to Do

### NEVER Force Push State Files
```bash
# DON'T DO THIS - will overwrite secondary's state
git push --force secondary main
```

This will overwrite the secondary fork's workspace state with the primary fork's workspace state, breaking workflows.

### NEVER Untrack State Files
```bash
# DON'T DO THIS - breaks GitHub Actions workflows
git rm --cached state/*.csv state/*.json
```

State files MUST remain tracked for GitHub Actions to function properly.

## Verifying State Preservation

After syncing, verify that the secondary fork retained its state:

```bash
# Check the state files weren't changed
git log secondary/main --oneline -- state/

# Or clone secondary separately and inspect
git clone git@github.com:org/slack-ploughshare.git secondary-check
cd secondary-check
ls -lh state/
git log --oneline -- state/ | head -5
```

## Emergency Recovery

If you accidentally overwrote a fork's state, recover it:

```bash
# Find the last good commit before the overwrite
git log secondary/main --oneline -- state/

# Reset to that commit
git checkout <last-good-commit> -- state/

# Commit and push
git add state/
git commit -m "fix: restore state after accidental overwrite"
git push secondary HEAD:main
```

## Automation Considerations

Each repository runs GitHub Actions independently for different Slack workspaces.

The workflows commit state updates automatically, so:
1. Never manually edit state files
2. Let workflows manage state persistence
3. Only sync code changes, never state changes
4. Review state file changes before pushing between forks

## Best Practices

If you're unsure about a sync operation:
1. Create a test branch first
2. Verify state files before force pushing
3. Keep backups of state files if doing risky operations
4. Check workflow runs after syncing to ensure nothing broke

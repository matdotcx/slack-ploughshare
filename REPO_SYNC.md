# Repository Sync Guide

This document explains how to sync code between the macadminsdotorg and matdotcx repositories whilst maintaining separate state data.

## Repository Structure

- **macadminsdotorg/slack-ploughshare** - Primary development repository
- **matdotcx/slack-ploughshare** - Original/backup repository

Both repositories maintain their own state files:
- `state/channel_analysis.csv`
- `state/channel_analysis.json`
- `state/channel_warnings.json`

These files are tracked in git (required for GitHub Actions workflows) but should remain separate between repositories.

## Why State Files Are Tracked

State files MUST be tracked in git because:
1. GitHub Actions workflows commit state updates after each run
2. This provides persistence across workflow executions
3. State history can be reviewed via git log
4. Each workspace (macadminsdotorg vs matdotcx) has different Slack data

## Syncing Code Between Repositories

When syncing code changes from macadminsdotorg to matdotcx (or vice versa), follow these steps to preserve each repository's state files.

### Option 1: Cherry-Pick Specific Commits (Recommended)

This is the safest method when you have specific commits to sync:

```bash
# In your macadminsdotorg clone
git remote add matdotcx git@github.com:matdotcx/slack-ploughshare.git
git fetch matdotcx

# Cherry-pick specific commits (excluding state file changes)
git cherry-pick <commit-hash>

# If the commit includes state file changes, unstage them:
git reset HEAD state/
git checkout -- state/

# Then push
git push matdotcx main
```

### Option 2: Push with State File Exclusion

When you want to push all commits but preserve matdotcx's state:

```bash
# In your macadminsdotorg clone
git remote add matdotcx git@github.com:matdotcx/slack-ploughshare.git

# Create a temporary branch with matdotcx's state files
git fetch matdotcx main
git checkout -b sync-to-matdotcx

# Get matdotcx's state files
git checkout matdotcx/main -- state/

# Commit the preserved state
git add state/
git commit -m "chore: preserve matdotcx state during sync"

# Push to matdotcx
git push matdotcx sync-to-matdotcx:main

# Clean up
git checkout main
git branch -D sync-to-matdotcx
```

### Option 3: Interactive Rebase (For Complex Syncs)

When you need to sync multiple commits whilst carefully managing state:

```bash
# In your macadminsdotorg clone
git remote add matdotcx git@github.com:matdotcx/slack-ploughshare.git
git fetch matdotcx

# Create sync branch
git checkout -b sync-to-matdotcx matdotcx/main

# Rebase your changes onto matdotcx
git rebase main

# During rebase, when conflicts occur in state/ files:
# Always keep matdotcx's version:
git checkout --theirs state/
git add state/
git rebase --continue

# Push to matdotcx
git push matdotcx sync-to-matdotcx:main --force-with-lease

# Clean up
git checkout main
git branch -D sync-to-matdotcx
```

## What NOT to Do

### NEVER Force Push State Files
```bash
# DON'T DO THIS - will overwrite matdotcx's state
git push --force matdotcx main
```

This will overwrite matdotcx's workspace state with macadminsdotorg's workspace state, breaking the matdotcx workflows.

### NEVER Untrack State Files
```bash
# DON'T DO THIS - breaks GitHub Actions workflows
git rm --cached state/*.csv state/*.json
```

State files MUST remain tracked for GitHub Actions to function properly.

## Verifying State Preservation

After syncing, verify that matdotcx retained its state:

```bash
# Check the state files weren't changed
git log matdotcx/main --oneline -- state/

# Or clone matdotcx separately and inspect
git clone git@github.com:matdotcx/slack-ploughshare.git matdotcx-check
cd matdotcx-check
ls -lh state/
git log --oneline -- state/ | head -5
```

## Emergency Recovery

If you accidentally overwrote matdotcx's state, recover it:

```bash
# Find the last good commit before the overwrite
git log matdotcx/main --oneline -- state/

# Reset to that commit
git checkout <last-good-commit> -- state/

# Commit and push
git add state/
git commit -m "fix: restore matdotcx state after accidental overwrite"
git push matdotcx HEAD:main
```

## Automation Considerations

Each repository runs GitHub Actions independently:
- **macadminsdotorg**: Monitors MacAdmins Slack workspace
- **matdotcx**: Monitors a different Slack workspace (or testing)

The workflows commit state updates automatically, so:
1. Never manually edit state files
2. Let workflows manage state persistence
3. Only sync code changes, never state changes
4. Review state file changes before pushing between repos

## Questions?

If you're unsure about a sync operation:
1. Create a test branch first
2. Verify state files before force pushing
3. Keep backups of state files if doing risky operations
4. Check workflow runs after syncing to ensure nothing broke

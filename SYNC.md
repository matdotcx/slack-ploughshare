# Repository Synchronisation Guide

This repository maintains two Git remotes with different purposes and configurations.

## Repository Structure

### macadminsdotorg/slack-ploughshare (origin)
- **Purpose**: Production deployment for MacAdmins Slack workspace
- **State Management**: State files tracked in Git (required for GitHub Actions)
- **Workflow**: Automated via GitHub Actions with state persistence
- **URL**: git@github.com:macadminsdotorg/slack-ploughshare.git

### matdotcx/slack-ploughshare (matdotcx)
- **Purpose**: Development fork and backup
- **State Management**: State files excluded via .gitignore
- **Workflow**: Manual/local development
- **URL**: git@github.com:matdotcx/slack-ploughshare.git

## Key Differences

| Aspect | macadminsdotorg | matdotcx |
|--------|----------------|----------|
| State files | Tracked in git | Ignored (.gitignore) |
| Commits | Code + state updates | Code only |
| Purpose | Production automation | Development |
| Branch structure | Linear with state commits | Clean code history |

## Synchronisation Strategy

### What to Sync
- **Code changes** (*.py, *.yml, *.yaml, *.md)
- **Configuration examples** (*.example files)
- **Documentation updates**

### What NOT to Sync
- **State files** (state/*.json, state/*.csv) - only in macadminsdotorg
- **Workflow state commits** - only in macadminsdotorg
- **Environment files** (.env, .env.*)

## Manual Sync Process

### 1. After Making Code Changes

When you've made code changes and committed to `origin` (macadminsdotorg):

```bash
# Ensure you're on main with latest changes
git checkout main
git pull origin main

# Create temporary branch from matdotcx/main
git fetch matdotcx
git checkout -b sync-to-matdotcx matdotcx/main

# Cherry-pick only code commits (skip state commits)
git cherry-pick <commit-hash>

# Push to matdotcx
git push matdotcx sync-to-matdotcx:main

# Return to main and clean up
git checkout main
git branch -D sync-to-matdotcx
```

### 2. Automated Sync (Recommended)

Use the provided `sync-repos.sh` script:

```bash
# Sync the most recent code commit
./sync-repos.sh

# Sync a specific commit
./sync-repos.sh <commit-hash>

# Sync multiple commits
./sync-repos.sh <commit1> <commit2> <commit3>
```

## Sync Script Usage

The `sync-repos.sh` script automates the cherry-pick process:

```bash
#!/bin/bash
# Automatically syncs code commits from origin to matdotcx
# Skips state-only commits automatically
```

### Features
- Validates commit exists before syncing
- Skips state-only commits (e.g., "Update state from workflow run")
- Handles cherry-pick conflicts gracefully
- Automatically cleans up temporary branches

## Identifying Commits to Sync

### Code Commits (SYNC these)
```
fix: improve clarity of reaction check results message
feat: post check-reactions results to Slack channel
docs: update README with dual-token architecture
refactor: extract warning message builder
```

### State Commits (SKIP these)
```
Update state from workflow run #14
Update state from workflow run #13
```

## Workflow Examples

### After Bug Fix
```bash
# 1. Fix bug and commit to origin
git add slack_channel_analytics.py
git commit -m "fix: handle missing reaction data gracefully"
git push origin main

# 2. Sync to matdotcx
./sync-repos.sh  # Syncs latest commit
```

### After Feature Development
```bash
# 1. Develop feature with multiple commits
git add .
git commit -m "feat: add channel merge detection"
git commit -m "test: add tests for merge detection"
git commit -m "docs: document merge detection feature"
git push origin main

# 2. Get commit hashes for all feature commits
git log --oneline -3

# 3. Sync all feature commits
./sync-repos.sh <hash1> <hash2> <hash3>
```

### After State Update (Automated Workflow)
```bash
# GitHub Actions commits state update
# Commit: "Update state from workflow run #X"

# NO ACTION NEEDED - state commits stay only in macadminsdotorg
```

## Conflict Resolution

If cherry-pick fails due to conflicts:

```bash
# 1. Review conflicts
git status

# 2. Resolve conflicts manually
vim <conflicted-file>

# 3. Continue cherry-pick
git add <resolved-files>
git cherry-pick --continue

# 4. Push to matdotcx
git push matdotcx HEAD:main

# 5. Clean up
git checkout main
git branch -D sync-to-matdotcx
```

## Verification

After syncing, verify both repos have the code changes:

```bash
# Fetch both remotes
git fetch origin
git fetch matdotcx

# Compare specific file
git diff origin/main:slack_channel_analytics.py matdotcx/main:slack_channel_analytics.py

# Check recent commits
git log --oneline --graph --all --decorate -10
```

## Best Practices

1. **Commit code and state separately** - Don't mix code changes with state updates
2. **Use descriptive commit messages** - Makes it easier to identify what to sync
3. **Sync frequently** - Don't let repos drift too far apart
4. **Test before syncing** - Ensure code works in macadminsdotorg before syncing to matdotcx
5. **Review the diff** - Before pushing to matdotcx, review what's changing

## Architecture Decision

**Why maintain two repositories?**

The macadminsdotorg repo uses GitHub Actions for automation, which requires state persistence in git to maintain warning/archive tracking across workflow runs. The matdotcx fork is used for development and doesn't need state file bloat in git history, so state files are excluded via .gitignore.

This dual-repo approach provides:
- Clean development history in matdotcx
- Production-ready automation in macadminsdotorg
- Separation of concerns between code and state
- Flexibility for different deployment patterns

#!/bin/bash
# sync-repos.sh - Synchronise code commits from origin to matdotcx
#
# Usage:
#   ./sync-repos.sh              # Sync latest commit from origin/main
#   ./sync-repos.sh <commit>     # Sync specific commit
#   ./sync-repos.sh <c1> <c2>    # Sync multiple commits

set -e  # Exit on error

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Colour

# Configuration
ORIGIN_REMOTE="origin"
MATDOTCX_REMOTE="matdotcx"
TEMP_BRANCH="sync-to-matdotcx-$(date +%s)"

# State commit patterns to skip
STATE_COMMIT_PATTERNS=(
  "Update state from workflow run"
  "State update:"
)

# Function to print coloured messages
print_info() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if commit is a state-only commit
is_state_commit() {
  local commit=$1
  local commit_message=$(git log -1 --format=%s "$commit")

  for pattern in "${STATE_COMMIT_PATTERNS[@]}"; do
    if [[ "$commit_message" == *"$pattern"* ]]; then
      return 0  # Is a state commit
    fi
  done

  return 1  # Not a state commit
}

# Function to clean up on exit
cleanup() {
  local exit_code=$?

  # Return to main branch
  if git rev-parse --verify main >/dev/null 2>&1; then
    git checkout main 2>/dev/null || true
  fi

  # Delete temp branch if it exists
  if git rev-parse --verify "$TEMP_BRANCH" >/dev/null 2>&1; then
    git branch -D "$TEMP_BRANCH" 2>/dev/null || true
  fi

  if [ $exit_code -eq 0 ]; then
    print_info "Cleanup complete"
  else
    print_warn "Cleanup complete (script failed)"
  fi
}

trap cleanup EXIT

# Validate we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  print_error "Not in a git repository"
  exit 1
fi

# Validate remotes exist
if ! git remote get-url "$ORIGIN_REMOTE" >/dev/null 2>&1; then
  print_error "Remote '$ORIGIN_REMOTE' not found"
  exit 1
fi

if ! git remote get-url "$MATDOTCX_REMOTE" >/dev/null 2>&1; then
  print_error "Remote '$MATDOTCX_REMOTE' not found"
  exit 1
fi

# Fetch latest from both remotes
print_info "Fetching from remotes..."
git fetch "$ORIGIN_REMOTE"
git fetch "$MATDOTCX_REMOTE"

# Determine commits to sync
COMMITS_TO_SYNC=()

if [ $# -eq 0 ]; then
  # No arguments - sync latest commit from origin/main
  LATEST_COMMIT=$(git rev-parse "$ORIGIN_REMOTE/main")
  print_info "No commits specified, using latest from $ORIGIN_REMOTE/main: $LATEST_COMMIT"
  COMMITS_TO_SYNC=("$LATEST_COMMIT")
else
  # Use provided commits
  COMMITS_TO_SYNC=("$@")
fi

# Filter out state-only commits
VALID_COMMITS=()
for commit in "${COMMITS_TO_SYNC[@]}"; do
  # Validate commit exists
  if ! git rev-parse --verify "$commit" >/dev/null 2>&1; then
    print_error "Commit '$commit' not found"
    exit 1
  fi

  # Check if it's a state commit
  if is_state_commit "$commit"; then
    commit_short=$(git rev-parse --short "$commit")
    commit_msg=$(git log -1 --format=%s "$commit")
    print_warn "Skipping state commit $commit_short: $commit_msg"
  else
    VALID_COMMITS+=("$commit")
  fi
done

# Check if we have any valid commits to sync
if [ ${#VALID_COMMITS[@]} -eq 0 ]; then
  print_warn "No valid code commits to sync (all commits were state updates)"
  exit 0
fi

print_info "Will sync ${#VALID_COMMITS[@]} commit(s):"
for commit in "${VALID_COMMITS[@]}"; do
  commit_short=$(git rev-parse --short "$commit")
  commit_msg=$(git log -1 --format=%s "$commit")
  echo "  - $commit_short: $commit_msg"
done

# Create temporary branch from matdotcx/main
print_info "Creating temporary branch '$TEMP_BRANCH' from $MATDOTCX_REMOTE/main"
git checkout -b "$TEMP_BRANCH" "$MATDOTCX_REMOTE/main"

# Cherry-pick each commit
CHERRY_PICK_FAILED=0
for commit in "${VALID_COMMITS[@]}"; do
  commit_short=$(git rev-parse --short "$commit")
  commit_msg=$(git log -1 --format=%s "$commit")

  print_info "Cherry-picking $commit_short: $commit_msg"

  if git cherry-pick "$commit"; then
    print_info "Successfully cherry-picked $commit_short"
  else
    print_error "Cherry-pick failed for $commit_short"
    print_warn "Please resolve conflicts manually:"
    print_warn "  1. Fix conflicts in the listed files"
    print_warn "  2. Run: git add <resolved-files>"
    print_warn "  3. Run: git cherry-pick --continue"
    print_warn "  4. Run: git push $MATDOTCX_REMOTE $TEMP_BRANCH:main"
    print_warn "  5. Run: git checkout main && git branch -D $TEMP_BRANCH"
    CHERRY_PICK_FAILED=1
    exit 1
  fi
done

if [ $CHERRY_PICK_FAILED -eq 0 ]; then
  # Push to matdotcx
  print_info "Pushing to $MATDOTCX_REMOTE/main"
  git push "$MATDOTCX_REMOTE" "$TEMP_BRANCH:main"

  print_info "Successfully synced ${#VALID_COMMITS[@]} commit(s) to $MATDOTCX_REMOTE"

  # Show final state
  print_info "Verifying sync..."
  git fetch "$MATDOTCX_REMOTE"

  echo ""
  print_info "Repository status:"
  git log --oneline --graph --decorate "$MATDOTCX_REMOTE/main" -5
fi

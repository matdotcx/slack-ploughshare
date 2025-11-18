# Utility Scripts

This directory contains utility scripts for Slack Ploughshare operations.

## undo_warnings.py

Delete warning messages that were previously sent to channels.

**Requirements:**
- User token (xoxp-...) with `admin` and `chat:write` scopes
- Bot tokens cannot delete messages from channels they're not members of

**Usage:**

Test with a few channels first:
```bash
python3 scripts/undo_warnings.py --for-real --limit 5
```

Delete all warning messages:
```bash
python3 scripts/undo_warnings.py --for-real
```

**Via GitHub Actions:**

Use the "Manual: Undo Warnings" workflow for a safer, tracked execution:
- Requires typing "CONFIRM"
- Option to limit number of channels (for testing)
- Option to automatically clear warning tracker after deletion
- Commits changes to repository

**When to use:**
- Need to delete incorrect warning messages
- Want to clear all warnings and start fresh
- Testing warning message changes

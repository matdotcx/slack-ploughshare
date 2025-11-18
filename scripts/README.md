# Utility Scripts

This directory contains utility scripts for Slack Ploughshare operations.

## add_test_channels.py

Add fake test channels to the analysis file to verify warning messages.

**Purpose:**
Test that each category (very_old, dormant, never_used) receives the correct warning message without affecting real channels.

**Usage:**

Add test channels:
```bash
python3 scripts/add_test_channels.py --create-test-channels
```

This adds three fake channels:
- `TEST_VERY_OLD` - 600 days inactive (very_old category)
- `TEST_DORMANT` - 400 days inactive (dormant category)
- `TEST_NEVER_USED` - never used (never_used category)

Test warnings (dry run):
```bash
python slack_channel_analytics.py --send-warnings
```

Remove test channels when done:
```bash
python3 scripts/add_test_channels.py --remove-test-channels
```

**Note:** These channel IDs are fake (start with `TEST_`) and won't post messages to real channels. The script will fail to send to them, but you can verify the correct message is attempted for each category in the logs.

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

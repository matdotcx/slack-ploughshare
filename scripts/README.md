# Utility Scripts

This directory contains utility scripts for Slack Ploughshare operations.

## add_test_channels.py

Add test channels to the analysis file to verify warning messages.

**Purpose:**
Test that each category (very_old, dormant, never_used) receives the correct warning message.

**Usage:**

### Option 1: Fake Channel IDs (safest - won't post to real channels)

Add test channels with fake IDs:
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

**Note:** Fake channel IDs start with `TEST_` and won't post messages to real channels. The script will fail to send to them, but you can verify the correct message template is attempted for each category in the logs.

### Option 2: Real Channel IDs (posts actual test messages)

**Step 1:** Create test channels in Slack:
- `#test-very-old-warning`
- `#test-dormant-warning`
- `#test-never-used-warning`

**Step 2a:** Auto-fetch channel IDs from Slack:
```bash
python3 scripts/add_test_channels.py --create-test-channels --with-real-channels
```

**Step 2b:** Or manually specify channel IDs:
```bash
python3 scripts/add_test_channels.py --create-test-channels \
  --very-old-id C123456 --dormant-id C234567 --never-used-id C345678
```

**Step 3:** Test warnings (dry run first):
```bash
python slack_channel_analytics.py --send-warnings
python slack_channel_analytics.py --send-warnings --for-real
```

**Step 4:** Check Slack to verify correct messages were posted to each test channel

**Benefits of real channels:**
- See actual messages posted to Slack
- Verify message formatting and content
- Test full end-to-end flow

### Clean Up

Remove test channels from analysis when done:
```bash
python3 scripts/add_test_channels.py --remove-test-channels
```

This removes both fake (`TEST_*`) and real test channel entries.

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

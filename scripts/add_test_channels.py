#!/usr/bin/env python3
"""
Add test channels to the analysis file for testing warning messages.

This script adds test channels to state/channel_analysis.json so you can
verify that the correct category-specific warning messages are sent.

Usage:
  # Use fake channel IDs (safe, won't post to real channels)
  python3 scripts/add_test_channels.py --create-test-channels

  # Use real Slack channel IDs (will post to real test channels)
  python3 scripts/add_test_channels.py --create-test-channels --with-real-channels

  # Or specify channel IDs manually
  python3 scripts/add_test_channels.py --create-test-channels \\
    --very-old-id C123456 --dormant-id C234567 --never-used-id C345678
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from slack_sdk import WebClient
from dotenv import load_dotenv


def get_channel_ids_from_slack():
    """Fetch real channel IDs from Slack by looking for test channel names."""
    load_dotenv()
    token = os.getenv("SLACK_BOT_TOKEN")

    if not token:
        print("Error: SLACK_BOT_TOKEN not found in .env file")
        print("Cannot fetch real channel IDs without Slack token")
        return None

    client = WebClient(token=token)

    test_channel_names = {
        "test-very-old-warning": "very_old",
        "test-dormant-warning": "dormant",
        "test-never-used-warning": "never_used",
    }

    channel_ids = {}

    try:
        # Fetch all channels with pagination
        cursor = None
        total_checked = 0

        while True:
            response = client.conversations_list(
                types="public_channel,private_channel",
                limit=1000,
                cursor=cursor
            )

            for channel in response["channels"]:
                total_checked += 1
                channel_name = channel["name"]
                if channel_name in test_channel_names:
                    category = test_channel_names[channel_name]
                    channel_ids[category] = {
                        "id": channel["id"],
                        "name": channel_name
                    }
                    print(f"Found #{channel_name}: {channel['id']}")

            # Check if all found
            if len(channel_ids) == len(test_channel_names):
                print(f"All test channels found (checked {total_checked} channels)")
                return channel_ids

            # Check for more pages
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        # Some channels missing
        missing = [name for name in test_channel_names if test_channel_names[name] not in channel_ids]
        if missing:
            print(f"\nWarning: Could not find these test channels in Slack:")
            for name in missing:
                print(f"  - #{name}")
            print(f"\nChecked {total_checked} channels total.")
            print("\nCreate them in Slack first, then run this script again.")
            return None

        return channel_ids

    except Exception as e:
        print(f"Error fetching channels from Slack: {e}")
        return None


def add_test_channels(channel_ids=None):
    """Add test channels to the analysis file with specific inactivity periods.

    Args:
        channel_ids: Dict mapping category -> {id, name} or None for fake IDs
    """

    analysis_file = Path("state/channel_analysis.json")

    if not analysis_file.exists():
        print(f"Error: {analysis_file} not found")
        print("Run a full analysis first to create the base file")
        return

    with open(analysis_file, "r") as f:
        data = json.load(f)

    # Determine if using real or fake channel IDs
    if channel_ids:
        print("\nUsing REAL Slack channel IDs - warnings will be posted to actual channels!")
        very_old_id = channel_ids["very_old"]["id"]
        very_old_name = channel_ids["very_old"]["name"]
        dormant_id = channel_ids["dormant"]["id"]
        dormant_name = channel_ids["dormant"]["name"]
        never_used_id = channel_ids["never_used"]["id"]
        never_used_name = channel_ids["never_used"]["name"]
    else:
        print("\nUsing FAKE channel IDs - warnings will NOT post to real channels")
        very_old_id = "TEST_VERY_OLD"
        very_old_name = "test-very-old-warning"
        dormant_id = "TEST_DORMANT"
        dormant_name = "test-dormant-warning"
        never_used_id = "TEST_NEVER_USED"
        never_used_name = "test-never-used-warning"

    # Create test channels with different inactivity periods
    test_channels = [
        {
            "channel_id": very_old_id,
            "channel_name": very_old_name,
            "days_since_last_message": 600,  # 20 months (very_old threshold is 550)
            "category": "very_old",
            "last_message_date": (datetime.now() - timedelta(days=600)).isoformat(),
        },
        {
            "channel_id": dormant_id,
            "channel_name": dormant_name,
            "days_since_last_message": 400,  # 13 months (dormant threshold is 380)
            "category": "dormant",
            "last_message_date": (datetime.now() - timedelta(days=400)).isoformat(),
        },
        {
            "channel_id": never_used_id,
            "channel_name": never_used_name,
            "days_since_last_message": 0,
            "category": "never_used",
            "has_messages": False,
            "last_message_date": None,
        },
    ]

    # Add common fields to test channels
    now_iso = datetime.now().isoformat()
    for channel in test_channels:
        channel.update({
            "is_private": False,
            "is_archived": False,
            "member_count": 1,
            "has_messages": channel.get("has_messages", True),
            "created_date": (datetime.now() - timedelta(days=365)).isoformat(),
            "days_old": 365,
            "pinned_count": 0,
            "warned_at": None,
            "archive_scheduled_for": None,
            "saved_by_reaction": False,
            "warning_status": None,
            "reactions_found": [],
            "topic": "TEST CHANNEL - Safe to delete",
            "purpose": "TEST CHANNEL - Safe to delete",
        })

    # Add test channels to appropriate categories
    for test_channel in test_channels:
        category = test_channel["category"]
        if category in data["categories"]:
            # Check if already exists
            existing_ids = [ch["channel_id"] for ch in data["categories"][category]]
            if test_channel["channel_id"] not in existing_ids:
                data["categories"][category].append(test_channel)
                print(f"Added test channel: #{test_channel['channel_name']} to '{category}' category")
                print(f"  Days inactive: {test_channel['days_since_last_message']}")

    # Update summary
    data["summary"]["very_old"] = len(data["categories"]["very_old"])
    data["summary"]["dormant"] = len(data["categories"]["dormant"])
    data["summary"]["never_used"] = len(data["categories"]["never_used"])

    # Save updated analysis
    with open(analysis_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nUpdated {analysis_file}")

    if channel_ids:
        print("\nTest channels added with REAL Slack IDs:")
        print(f"  - #{very_old_name} ({very_old_id}) - 600 days inactive")
        print(f"  - #{dormant_name} ({dormant_id}) - 400 days inactive")
        print(f"  - #{never_used_name} ({never_used_id}) - never used")
        print("\nNext steps:")
        print("  1. Dry run: python slack_channel_analytics.py --send-warnings")
        print("  2. Execute: python slack_channel_analytics.py --send-warnings --for-real")
        print("  3. Check Slack to verify correct messages posted")
        print("  4. Remove test channels: python3 scripts/add_test_channels.py --remove-test-channels")
    else:
        print("\nTest channels added. These channel IDs are fake and safe to test with:")
        print("  - TEST_VERY_OLD (600 days inactive)")
        print("  - TEST_DORMANT (400 days inactive)")
        print("  - TEST_NEVER_USED (never used)")
        print("\nNext steps:")
        print("  1. Run: python slack_channel_analytics.py --send-warnings")
        print("  2. Check logs to verify message templates")
        print("  3. Remove test channels: python3 scripts/add_test_channels.py --remove-test-channels")


def remove_test_channels():
    """Remove test channels from the analysis file."""

    analysis_file = Path("state/channel_analysis.json")

    if not analysis_file.exists():
        print(f"Error: {analysis_file} not found")
        return

    with open(analysis_file, "r") as f:
        data = json.load(f)

    # Test channel names to look for (both fake and real)
    test_names = {"test-very-old-warning", "test-dormant-warning", "test-never-used-warning"}

    removed_count = 0
    for category in ["very_old", "dormant", "never_used", "active"]:
        if category in data["categories"]:
            original_count = len(data["categories"][category])
            data["categories"][category] = [
                ch for ch in data["categories"][category]
                if not (ch["channel_id"].startswith("TEST_") or ch["channel_name"] in test_names)
            ]
            removed = original_count - len(data["categories"][category])
            removed_count += removed
            if removed > 0:
                print(f"Removed {removed} test channel(s) from '{category}' category")

    # Update summary
    data["summary"]["very_old"] = len(data["categories"]["very_old"])
    data["summary"]["dormant"] = len(data["categories"]["dormant"])
    data["summary"]["never_used"] = len(data["categories"]["never_used"])
    data["summary"]["active"] = len(data["categories"]["active"])

    with open(analysis_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nRemoved {removed_count} test channel(s) total")
    print(f"Updated {analysis_file}")


if __name__ == "__main__":
    if "--create-test-channels" in sys.argv:
        # Check for options
        use_real_channels = "--with-real-channels" in sys.argv
        manual_ids = {}

        # Check for manually specified IDs
        if "--very-old-id" in sys.argv:
            idx = sys.argv.index("--very-old-id")
            if idx + 1 < len(sys.argv):
                manual_ids["very_old"] = {
                    "id": sys.argv[idx + 1],
                    "name": "test-very-old-warning"
                }

        if "--dormant-id" in sys.argv:
            idx = sys.argv.index("--dormant-id")
            if idx + 1 < len(sys.argv):
                manual_ids["dormant"] = {
                    "id": sys.argv[idx + 1],
                    "name": "test-dormant-warning"
                }

        if "--never-used-id" in sys.argv:
            idx = sys.argv.index("--never-used-id")
            if idx + 1 < len(sys.argv):
                manual_ids["never_used"] = {
                    "id": sys.argv[idx + 1],
                    "name": "test-never-used-warning"
                }

        # Determine which IDs to use
        if manual_ids:
            # Manual IDs provided
            if len(manual_ids) != 3:
                print("Error: Must provide all three channel IDs:")
                print("  --very-old-id C123456 --dormant-id C234567 --never-used-id C345678")
                sys.exit(1)
            add_test_channels(channel_ids=manual_ids)
        elif use_real_channels:
            # Fetch from Slack
            print("Fetching channel IDs from Slack...")
            real_ids = get_channel_ids_from_slack()
            if real_ids:
                add_test_channels(channel_ids=real_ids)
            else:
                print("\nFailed to fetch channel IDs. Create these channels in Slack first:")
                print("  - #test-very-old-warning")
                print("  - #test-dormant-warning")
                print("  - #test-never-used-warning")
                sys.exit(1)
        else:
            # Use fake IDs
            add_test_channels()

    elif "--remove-test-channels" in sys.argv:
        remove_test_channels()

    else:
        print("Usage:")
        print("  # Use fake channel IDs (safe, won't post to real channels)")
        print("  python3 scripts/add_test_channels.py --create-test-channels")
        print()
        print("  # Auto-fetch real channel IDs from Slack")
        print("  python3 scripts/add_test_channels.py --create-test-channels --with-real-channels")
        print()
        print("  # Manually specify channel IDs")
        print("  python3 scripts/add_test_channels.py --create-test-channels \\")
        print("    --very-old-id C123456 --dormant-id C234567 --never-used-id C345678")
        print()
        print("  # Remove test channels")
        print("  python3 scripts/add_test_channels.py --remove-test-channels")

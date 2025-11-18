#!/usr/bin/env python3
"""
Add test channels to the analysis file for testing warning messages.

This script adds fake test channels to state/channel_analysis.json so you can
verify that the correct category-specific warning messages are sent.

Usage:
  python3 scripts/add_test_channels.py --create-test-channels
"""

import json
from datetime import datetime, timedelta
from pathlib import Path


def add_test_channels():
    """Add test channels to the analysis file with specific inactivity periods."""

    analysis_file = Path("state/channel_analysis.json")

    if not analysis_file.exists():
        print(f"Error: {analysis_file} not found")
        print("Run a full analysis first to create the base file")
        return

    with open(analysis_file, "r") as f:
        data = json.load(f)

    # Create test channels with different inactivity periods
    test_channels = [
        {
            "channel_id": "TEST_VERY_OLD",
            "channel_name": "test-very-old-warning",
            "days_since_last_message": 600,  # 20 months (very_old threshold is 550)
            "category": "very_old",
            "last_message_date": (datetime.now() - timedelta(days=600)).isoformat(),
        },
        {
            "channel_id": "TEST_DORMANT",
            "channel_name": "test-dormant-warning",
            "days_since_last_message": 400,  # 13 months (dormant threshold is 380)
            "category": "dormant",
            "last_message_date": (datetime.now() - timedelta(days=400)).isoformat(),
        },
        {
            "channel_id": "TEST_NEVER_USED",
            "channel_name": "test-never-used-warning",
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
    print("\nTest channels added. These channel IDs are fake and safe to test with:")
    print("  - TEST_VERY_OLD (600 days inactive)")
    print("  - TEST_DORMANT (400 days inactive)")
    print("  - TEST_NEVER_USED (never used)")
    print("\nNext steps:")
    print("  1. Run: python slack_channel_analytics.py --send-warnings")
    print("  2. Check that each test channel gets the correct message")
    print("  3. Remove test channels before production use")


def remove_test_channels():
    """Remove test channels from the analysis file."""

    analysis_file = Path("state/channel_analysis.json")

    if not analysis_file.exists():
        print(f"Error: {analysis_file} not found")
        return

    with open(analysis_file, "r") as f:
        data = json.load(f)

    removed_count = 0
    for category in ["very_old", "dormant", "never_used", "active"]:
        if category in data["categories"]:
            original_count = len(data["categories"][category])
            data["categories"][category] = [
                ch for ch in data["categories"][category]
                if not ch["channel_id"].startswith("TEST_")
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
    import sys

    if "--create-test-channels" in sys.argv:
        add_test_channels()
    elif "--remove-test-channels" in sys.argv:
        remove_test_channels()
    else:
        print("Usage:")
        print("  python3 scripts/add_test_channels.py --create-test-channels")
        print("  python3 scripts/add_test_channels.py --remove-test-channels")

#!/usr/bin/env python3
"""
Undo/Delete warning messages that were sent to channels.
Reads from state/channel_warnings.json and deletes messages using Slack API.

Requires: User token with 'admin' and 'chat:write' scopes (bot tokens cannot
delete messages from channels they're not members of).

Usage:
  python3 scripts/undo_warnings.py              # Delete all warnings
  python3 scripts/undo_warnings.py --limit 5    # Test with 5 channels first
  python3 scripts/undo_warnings.py --for-real   # Required for actual deletion
"""

import json
import os
import sys
from pathlib import Path
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import time


def main():
    # Load environment
    load_dotenv()

    # Check for --for-real flag
    if "--for-real" not in sys.argv:
        print("ERROR: This script requires --for-real flag to execute")
        print("Usage: python3 scripts/undo_warnings.py --for-real [--limit N]")
        print("\nThis is a safety measure to prevent accidental deletions.")
        sys.exit(1)

    # Prefer user token for deletions (has better permissions)
    token = os.getenv("SLACK_USER_TOKEN") or os.getenv("SLACK_BOT_TOKEN")

    if not token:
        print("Error: Neither SLACK_USER_TOKEN nor SLACK_BOT_TOKEN found in .env file")
        print("Add a user token (xoxp-...) with admin and chat:write scopes to delete messages")
        sys.exit(1)

    token_type = "user" if token.startswith("xoxp-") else "bot"
    print(f"Using {token_type} token")

    if token_type == "bot":
        print("WARNING: Bot tokens cannot delete messages from channels they're not in.")
        print("Add SLACK_USER_TOKEN (xoxp-...) to .env file for deletions to work.")
        sys.exit(1)

    client = WebClient(token=token)

    # Load warning tracker
    tracker_path = Path("state/channel_warnings.json")
    if not tracker_path.exists():
        print(f"Error: {tracker_path} not found")
        sys.exit(1)

    with open(tracker_path, "r") as f:
        data = json.load(f)

    channels = data.get("channels", {})

    if not channels:
        print("No warnings found in tracker")
        sys.exit(0)

    # Check for --limit argument
    limit = None
    if "--limit" in sys.argv:
        try:
            limit_idx = sys.argv.index("--limit")
            limit = int(sys.argv[limit_idx + 1])
            print(f"[TEST MODE] Limiting to {limit} channel(s)")
        except (IndexError, ValueError):
            print("Error: --limit requires a number (e.g., --limit 5)")
            sys.exit(1)

    print(f"\nFound {len(channels)} channels with warnings")
    if limit:
        print(f"Will delete from first {limit} channel(s) only\n")
    else:
        print("Deleting from ALL channels\n")

    print("Starting deletion process...")
    print("-" * 70)

    deleted_count = 0
    failed_count = 0
    skipped_count = 0
    rate_limit_delay = 0.5  # 500ms delay between deletions
    processed = 0

    for i, (channel_id, channel_data) in enumerate(channels.items(), 1):
        # Stop if we've hit the limit
        if limit and processed >= limit:
            print(f"\n[TEST MODE] Reached limit of {limit} channel(s), stopping...")
            break

        message_ts = channel_data.get("warning_message_ts")
        channel_name = channel_data.get("channel_name", channel_id)

        if not message_ts:
            print(f"  [{i}/{len(channels)}] [SKIP] No message timestamp for #{channel_name}")
            skipped_count += 1
            continue

        processed += 1

        try:
            client.chat_delete(
                channel=channel_id,
                ts=message_ts
            )
            print(f"  [{i}/{len(channels)}] [DELETED] #{channel_name}")
            deleted_count += 1
            time.sleep(rate_limit_delay)
        except SlackApiError as e:
            error_msg = e.response["error"]
            if error_msg == "ratelimited":
                retry_after = int(e.response.headers.get("Retry-After", 30))
                print(f"  [{i}/{len(channels)}] [RATE LIMITED] Waiting {retry_after}s...")
                time.sleep(retry_after)
                # Retry this deletion
                try:
                    client.chat_delete(channel=channel_id, ts=message_ts)
                    print(f"  [{i}/{len(channels)}] [DELETED] #{channel_name} (retry)")
                    deleted_count += 1
                    time.sleep(rate_limit_delay)
                except SlackApiError as retry_error:
                    print(f"  [{i}/{len(channels)}] [FAILED] #{channel_name}: {retry_error.response['error']}")
                    failed_count += 1
            else:
                print(f"  [{i}/{len(channels)}] [FAILED] #{channel_name}: {error_msg}")
                failed_count += 1

    print("-" * 70)
    print("\nSummary:")
    print(f"  Deleted:  {deleted_count}")
    print(f"  Failed:   {failed_count}")
    print(f"  Skipped:  {skipped_count}")
    print(f"  Total:    {len(channels)}")

    if not limit:
        print("\nNext steps:")
        print("  1. Clear the warning tracker:")
        print("     rm state/channel_warnings.json")
        print("     python -c 'from slack_channel_analytics import WarningTracker; WarningTracker()'")
        print("  2. Commit and push the cleared tracker")
        print("  3. Re-run warnings with corrected messages")


if __name__ == "__main__":
    main()

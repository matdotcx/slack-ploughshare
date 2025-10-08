#!/usr/bin/env python3
"""
Slack Channel Analytics & Cleanup Tool

Analyzes channels to identify abandoned ones and generates reports.
Can optionally archive channels based on criteria.
"""

import os
import json
import csv
import time
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def load_env():
    """Load environment variables from .env file."""
    env_path = Path.home() / ".env"
    if env_path.exists():
        load_dotenv(env_path)


def load_config(config_file=None):
    """Load configuration from YAML file."""
    if config_file is None:
        config_file = Path.cwd() / "slack_analytics_config.yaml"

    if config_file.exists():
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}

    # Set defaults if not provided
    defaults = {
        'analysis': {
            'days_dormant': 30,
            'days_very_old': 180,
            'include_private_channels': True,
        },
        'cleanup': {
            'include_very_old': True,
            'include_dormant': True,
            'include_never_used': True,
            'send_warning': True,
            'warning_days_before_archive': 30,
            'warning_message': 'This channel has been inactive and is scheduled for archival. React with 👍 within 30 days to keep it.',
        },
        'output': {
            'report_file': 'channel_analysis.json',
            'export_csv': True,
            'csv_file': 'channel_analysis.csv',
            'summary_limit': 15,
            'show_member_count': True,
            'show_last_message_date': True,
        },
        'logging': {
            'verbose': False,
            'show_rate_limits': True,
            'progress_interval': 50,
        },
        'rate_limiting': {
            'delay_between_requests_ms': 100,
            'smart_rate_limiting': True,
            'max_retries': 5,
        }
    }

    # Merge with defaults
    for section in defaults:
        if section not in config:
            config[section] = {}
        for key, value in defaults[section].items():
            if key not in config[section]:
                config[section][key] = value

    return config


class ChannelAnalyzer:
    def __init__(self, token, config=None):
        self.client = WebClient(token=token)
        self.channels = []
        self.analysis = []
        self.config = config or {}
        self.show_progress = False  # Flag to control progress display
        self.rate_limit_count = 0  # Track rate limits

    def fetch_all_channels(self, limit=None):
        """Fetch all channels (both public and private)."""
        print("Fetching channels...")
        channels = []
        cursor = None

        # Try to fetch both public and private channels
        # If groups:read scope is missing, fall back to public only
        channel_types = "public_channel,private_channel"

        while True:
            try:
                response = self.client.conversations_list(
                    limit=100,
                    cursor=cursor,
                    exclude_archived=True,
                    types=channel_types
                )
                channels.extend(response.get("channels", []))

                # Check if we've reached the limit
                if limit and len(channels) >= limit:
                    channels = channels[:limit]
                    break

                cursor = response.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
                print(f"  Fetched {len(channels)} channels so far...")
                time.sleep(0.5)  # Rate limiting
            except SlackApiError as e:
                if e.response['error'] == 'ratelimited':
                    wait_time = int(e.response.get('retry_after', 5))
                    print(f"  Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                elif e.response['error'] == 'missing_scope' and 'groups:read' in str(e):
                    # Fall back to public channels only
                    print("[WARNING] Missing 'groups:read' scope for private channels, analyzing public channels only")
                    channel_types = "public_channel"
                    cursor = None
                    channels = []
                    continue
                else:
                    raise

        self.channels = channels
        print(f"Fetched {len(channels)} channels\n")
        return channels

    def analyze_channel(self, channel):
        """Analyze a single channel for activity and metrics."""
        channel_id = channel['id']
        channel_name = channel['name']

        try:
            # Get channel info with member count
            info_response = self.client.conversations_info(
                channel=channel_id,
                include_num_members=True
            )
            channel_info = info_response['channel']

            # Get member count from channel info
            member_count = channel_info.get('num_members', 0)

            # For Business+ plans, we can't reliably get member counts
            # Focus on activity (last message) instead, which is more important for cleanup

            # Try to get message history and other details
            # These will fail gracefully if bot isn't in channel
            last_message_date = None
            days_since_last_message = None
            has_messages = False
            pinned_count = 0

            try:
                # Try to get message history (last message)
                history_response = self.client.conversations_history(
                    channel=channel_id,
                    limit=1
                )
                messages = history_response.get('messages', [])

                if messages:
                    last_message_ts = float(messages[0]['ts'])
                    last_message_date = datetime.fromtimestamp(last_message_ts)
                    days_since_last_message = (datetime.now() - last_message_date).days
                    has_messages = True
            except SlackApiError as e:
                if e.response['error'] not in ['not_in_channel', 'channel_not_found', 'access_denied', 'missing_scope']:
                    raise
                # If history access fails, note it but don't use fallbacks
                # (fallback timestamps are unreliable)

            try:
                # Get pinned items
                pinned_response = self.client.pins_list(channel=channel_id)
                pinned_count = len(pinned_response.get('items', []))
            except SlackApiError as e:
                if e.response['error'] not in ['not_in_channel', 'channel_not_found', 'access_denied', 'missing_scope']:
                    raise
                # If bot can't access pins, just use 0
                pinned_count = 0

            # Calculate metrics
            created_ts = channel_info.get('created')
            created_date = datetime.fromtimestamp(created_ts) if created_ts else None
            days_old = (datetime.now() - created_date).days if created_date else None

            analysis = {
                'channel_id': channel_id,
                'channel_name': channel_name,
                'is_private': channel_info.get('is_private', False),
                'created_date': created_date.isoformat() if created_date else None,
                'days_old': days_old,
                'member_count': member_count,
                'last_message_date': last_message_date.isoformat() if last_message_date else None,
                'days_since_last_message': days_since_last_message,
                'has_messages': has_messages,
                'pinned_count': pinned_count,
                'is_archived': channel_info.get('is_archived', False),
                'topic': channel_info.get('topic', {}).get('value', ''),
                'purpose': channel_info.get('purpose', {}).get('value', ''),
            }

            return analysis

        except SlackApiError as e:
            if e.response['error'] == 'ratelimited':
                wait_time = int(e.response.get('retry_after', 5))
                if not self.show_progress:
                    print(f"  Rate limited on {channel_name}, waiting {wait_time}s...")
                else:
                    self.rate_limit_count += 1
                time.sleep(wait_time)
                return self.analyze_channel(channel)  # Retry
            elif e.response['error'] == 'missing_scope':
                # On Business+ plan, may not have history access
                # Use what we have from channel_info
                created_ts = channel_info.get('created')
                created_date = datetime.fromtimestamp(created_ts) if created_ts else None
                days_old = (datetime.now() - created_date).days if created_date else None

                # Can't access message history, so we have no reliable activity data
                last_message_date = None
                days_since_last_message = None
                has_messages = False

                analysis = {
                    'channel_id': channel_id,
                    'channel_name': channel_name,
                    'is_private': channel_info.get('is_private', False),
                    'created_date': created_date.isoformat() if created_date else None,
                    'days_old': days_old,
                    'member_count': member_count,
                    'last_message_date': last_message_date.isoformat() if last_message_date else None,
                    'days_since_last_message': days_since_last_message,
                    'has_messages': has_messages,
                    'pinned_count': 0,
                    'is_archived': channel_info.get('is_archived', False),
                    'topic': channel_info.get('topic', {}).get('value', ''),
                    'purpose': channel_info.get('purpose', {}).get('value', ''),
                }
                return analysis
            else:
                print(f"  ⚠️  Error analyzing {channel_name}: {e.response['error']}")
                return None

    def print_progress(self, current_idx, total, current_channel, last_response, start_time, last_print_time=[0], first_print=[True]):
        """Print progress update (throttled to once per second)."""
        import sys

        # Only print once per second to avoid spam
        current_time = time.time()
        if current_time - last_print_time[0] < 1.0 and current_idx < total:
            return
        last_print_time[0] = current_time

        elapsed = datetime.now() - start_time
        elapsed_str = f"{int(elapsed.total_seconds() // 60)}m {int(elapsed.total_seconds() % 60)}s"

        next_channel = self.channels[current_idx + 1]['name'] if current_idx + 1 < len(self.channels) else "None"

        # Move cursor up and clear if not first print
        if not first_print[0]:
            sys.stdout.write('\033[11A')  # Move up 11 lines
            sys.stdout.write('\033[J')    # Clear from cursor down
        first_print[0] = False

        # Print the progress block
        print("\nChannel Analysis Progress")
        print("-" * 70)
        print(f"  Processed: {current_idx}/{total} channels")
        print(f"  Currently working on: #{current_channel['name']}")
        print(f"  Up next: #{next_channel}")
        print(f"  Time elapsed: {elapsed_str}")
        print(f"  Current API call: conversations.info")
        print(f"  Rate limits hit: {self.rate_limit_count}")
        print()
        print(f"  Last API response: {last_response}")

        sys.stdout.flush()

    def analyze_all_channels(self):
        """Analyze all channels."""
        import sys
        from datetime import datetime, timedelta

        self.analysis = []
        skipped = 0
        self.show_progress = True  # Enable progress mode
        self.rate_limit_count = 0  # Reset counter

        # Get configuration
        rate_config = self.config.get('rate_limiting', {})
        delay_ms = rate_config.get('delay_between_requests_ms', 100) / 1000.0

        start_time = datetime.now()
        last_api_response = "Starting"

        for i, channel in enumerate(self.channels):
            analysis = self.analyze_channel(channel)
            if analysis:
                self.analysis.append(analysis)
                last_api_response = "SUCCESS"
            else:
                skipped += 1
                last_api_response = "SKIPPED or ERROR"

            # Update progress
            self.print_progress(i + 1, len(self.channels), channel, last_api_response, start_time)

            # Apply rate limiting
            time.sleep(delay_ms)

        self.show_progress = False  # Disable progress mode

        print(f"\n\nAnalyzed {len(self.analysis)} channels (skipped {skipped} inaccessible channels)\n")
        return self.analysis

    def categorize_channels(self):
        """Categorize channels by activity status using config thresholds."""
        # Get thresholds from config
        analysis_config = self.config.get('analysis', {})
        days_inactive = analysis_config.get('days_dormant', 30)
        days_very_inactive = analysis_config.get('days_very_old', 180)

        categories = {
            'active': [],
            'dormant': [],
            'very_old': [],
            'never_used': [],
        }

        for channel in self.analysis:
            if channel['is_archived']:
                continue

            if not channel['has_messages']:
                categories['never_used'].append(channel)
            elif channel['days_since_last_message'] >= days_very_inactive:
                categories['very_old'].append(channel)
            elif channel['days_since_last_message'] >= days_inactive:
                categories['dormant'].append(channel)
            else:
                categories['active'].append(channel)

        return categories

    def export_to_csv(self, categories):
        """Export channel analysis to CSV."""
        output_config = self.config.get('output', {})
        csv_file = output_config.get('csv_file', 'channel_analysis.csv')

        # Flatten all categories into one list
        all_channels = []
        for category_name, channels in categories.items():
            for channel in channels:
                channel_data = channel.copy()
                channel_data['category'] = category_name
                all_channels.append(channel_data)

        if not all_channels:
            return

        # Define CSV columns
        fieldnames = [
            'channel_name',
            'channel_id',
            'category',
            'is_private',
            'is_archived',
            'member_count',
            'has_messages',
            'days_since_last_message',
            'last_message_date',
            'created_date',
            'days_old',
            'pinned_count',
            'topic',
            'purpose',
        ]

        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(all_channels)

    def generate_report(self):
        """Generate a detailed report."""
        output_config = self.config.get('output', {})
        output_file = output_config.get('report_file', 'channel_analysis.json')
        export_csv = output_config.get('export_csv', True)

        categories = self.categorize_channels()

        report = {
            'generated_at': datetime.now().isoformat(),
            'total_channels': len(self.channels),
            'analyzed_channels': len(self.analysis),
            'config': {
                'days_dormant': self.config.get('analysis', {}).get('days_dormant', 30),
                'days_very_old': self.config.get('analysis', {}).get('days_very_old', 180),
            },
            'summary': {
                'active': len(categories['active']),
                'dormant': len(categories['dormant']),
                'very_old': len(categories['very_old']),
                'never_used': len(categories['never_used']),
            },
            'categories': categories,
        }

        # Save JSON
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        # Export to CSV if enabled
        if export_csv:
            self.export_to_csv(categories)

        return report, categories

    def print_summary(self, categories):
        """Print a summary of findings."""
        output_config = self.config.get('output', {})
        summary_limit = output_config.get('summary_limit', 15)
        show_members = output_config.get('show_member_count', True)

        analysis_config = self.config.get('analysis', {})
        days_dormant = analysis_config.get('days_dormant', 30)
        days_very_old = analysis_config.get('days_very_old', 180)

        print("\nChannel Analysis Summary")
        print("=" * 70)
        print(f"\nAnalysis Date: {datetime.now().isoformat()}")
        print("Configuration:")
        print(f"  Days until dormant: {days_dormant}")
        print(f"  Days until very old: {days_very_old}")

        print("\nStatistics")
        print("-" * 70)
        print(f"Total channels analyzed:        {len(self.channels)}")
        print(f"Active channels:                 {len(categories['active'])}")
        print(f"Dormant channels ({days_dormant}+ days):     {len(categories['dormant'])}")
        print(f"Very old channels ({days_very_old}+ days):   {len(categories['very_old'])}")
        print(f"Never-used channels:              {len(categories['never_used'])}")

        cleanup_total = len(categories['dormant']) + len(categories['never_used']) + len(categories['very_old'])
        print(f"\nCleanup Candidates")
        print("-" * 70)
        print(f"Total channels eligible: {cleanup_total}\n")

        if categories['very_old']:
            print(f"Very Old Channels ({days_very_old}+ days inactive)  [{len(categories['very_old'])} channels]")
            print("." * 70)
            for channel in sorted(categories['very_old'], key=lambda x: x['days_since_last_message'], reverse=True)[:summary_limit]:
                last_msg = channel['last_message_date'][:10] if channel['last_message_date'] else 'N/A'
                members = channel['member_count'] if channel['member_count'] else '?'
                member_str = f"{members} members" if show_members else ""
                print(f"  {channel['channel_name']:<35} {member_str:<15} last msg: {last_msg}")
            if len(categories['very_old']) > summary_limit:
                print(f"  ... and {len(categories['very_old']) - summary_limit} more\n")
            else:
                print()

        if categories['dormant']:
            print(f"Dormant Channels ({days_dormant}+ days inactive)  [{len(categories['dormant'])} channels]")
            print("." * 70)
            for channel in sorted(categories['dormant'], key=lambda x: x['days_since_last_message'], reverse=True)[:summary_limit]:
                last_msg = channel['last_message_date'][:10] if channel['last_message_date'] else 'N/A'
                members = channel['member_count'] if channel['member_count'] else '?'
                member_str = f"{members} members" if show_members else ""
                print(f"  {channel['channel_name']:<35} {member_str:<15} last msg: {last_msg}")
            if len(categories['dormant']) > summary_limit:
                print(f"  ... and {len(categories['dormant']) - summary_limit} more\n")
            else:
                print()

        if categories['never_used']:
            print(f"Never-Used Channels  [{len(categories['never_used'])} channels]")
            print("." * 70)
            for channel in sorted(categories['never_used'], key=lambda x: x['created_date'], reverse=True)[:summary_limit]:
                created = channel['created_date'][:10] if channel['created_date'] else 'N/A'
                members = channel['member_count'] if channel['member_count'] else '?'
                member_str = f"{members} members" if show_members else ""
                print(f"  {channel['channel_name']:<35} {member_str:<15} created: {created}")
            if len(categories['never_used']) > summary_limit:
                print(f"  ... and {len(categories['never_used']) - summary_limit} more\n")
            else:
                print()

        print("=" * 70)

    def invite_bot_to_channel(self, channel_id, dry_run=True):
        """Invite the bot to a channel."""
        try:
            if dry_run:
                print(f"  [DRY RUN] Would invite bot to channel {channel_id}")
                return True
            else:
                self.client.conversations_join(channel=channel_id)
                print(f"  [SUCCESS] Invited bot to channel {channel_id}")
                return True
        except SlackApiError as e:
            print(f"  [ERROR] Failed to join {channel_id}: {e.response['error']}")
            return False

    def send_warning_message(self, channel_id, channel_name=None, dry_run=True):
        """Send a warning message to a channel before archiving."""
        cleanup_config = self.config.get('cleanup', {})
        send_warning = cleanup_config.get('send_warning', True)

        if not send_warning:
            return True

        warning_days = cleanup_config.get('warning_days_before_archive', 30)
        message = cleanup_config.get('warning_message', 'This channel is scheduled for archival.')

        # Replace placeholder
        from datetime import datetime, timedelta
        archive_date = (datetime.now() + timedelta(days=warning_days)).strftime('%Y-%m-%d')
        message = message.replace('{archive_date}', archive_date)

        name_str = f" - #{channel_name}" if channel_name else ""

        try:
            if dry_run:
                print(f"  [DRY RUN] Would send warning to {channel_id}{name_str}")
                print(f"    Message: {message[:80]}...")
                return True
            else:
                self.client.chat_postMessage(channel=channel_id, text=message)
                print(f"  [SUCCESS] Sent warning message to {channel_id}{name_str}")
                return True
        except SlackApiError as e:
            if dry_run:
                print(f"  [DRY RUN] Would send warning to {channel_id}{name_str}")
            else:
                print(f"  [ERROR] Failed to send warning to {channel_id}{name_str}: {e.response['error']}")
            return False

    def archive_channel(self, channel_id, channel_name=None, dry_run=True):
        """Archive a channel."""
        try:
            name_str = f" - #{channel_name}" if channel_name else ""
            if dry_run:
                print(f"  [DRY RUN] Would archive channel {channel_id}{name_str}")
                return True
            else:
                self.client.conversations_archive(channel=channel_id)
                print(f"  [SUCCESS] Archived channel {channel_id}{name_str}")
                return True
        except SlackApiError as e:
            print(f"  [ERROR] Failed to archive {channel_id}{name_str}: {e.response['error']}")
            return False


def main():
    import sys

    load_env()

    # Load configuration
    config = load_config()

    token = os.getenv("SLACK_BOT_TOKEN")

    if not token:
        print("Error: SLACK_BOT_TOKEN not found in .env file")
        return

    # Check for command line argument
    limit = None
    channel_id = None
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == '--limit' and len(sys.argv) > 2:
            try:
                limit = int(sys.argv[2])
                print(f"Limiting analysis to {limit} channels")
            except ValueError:
                print(f"Invalid limit: {sys.argv[2]}")
                return
        elif arg == '--channel' and len(sys.argv) > 2:
            channel_id = sys.argv[2]
            print(f"Analyzing single channel: {channel_id}")
        elif arg == '--join-channels':
            dry_run = True
            if len(sys.argv) > 2 and sys.argv[2] == '--for-real':
                dry_run = False
                print("⚠️  ACTUALLY joining all channels...")
            else:
                print("DRY RUN: Would join all channels for accurate data collection")
                print("To actually join, run: python slack_channel_analytics.py --join-channels --for-real")
            # This will be handled in main()
            analyzer = ChannelAnalyzer(token, config)
            analyzer.fetch_all_channels(limit=limit)
            print(f"\n{'Joining' if not dry_run else 'Would join'} {len(analyzer.channels)} channels...")
            for i, channel in enumerate(analyzer.channels, 1):
                if (i % 50) == 0:
                    print(f"  {'Joined' if not dry_run else 'Would join'} {i}/{len(analyzer.channels)} channels...")
                analyzer.invite_bot_to_channel(channel['id'], dry_run=dry_run)
                time.sleep(0.1)  # Rate limiting
            print(f"✅ Dry run complete" if dry_run else f"✅ Bot joined {len(analyzer.channels)} channels")
            return
        elif arg == '--send-warnings':
            print("Loading analysis from previous run...")
            # Try to load from saved report
            output_config = config.get('output', {})
            report_file = output_config.get('report_file', 'channel_analysis.json')

            if not Path(report_file).exists():
                print(f"No saved report found at {report_file}")
                print("Run analysis first: python slack_channel_analytics.py --limit 100")
                return

            with open(report_file, 'r') as f:
                report = json.load(f)

            analyzer = ChannelAnalyzer(token, config)

            # Send warnings to channels
            to_warn = report['categories']['very_old'] + report['categories']['never_used'] + report['categories']['dormant']

            dry_run = True
            if len(sys.argv) > 2 and sys.argv[2] == '--for-real':
                dry_run = False
                print("SENDING WARNINGS FOR REAL")
            else:
                print("DRY RUN: Would send warnings to channels")

            if to_warn:
                for channel in sorted(to_warn, key=lambda x: x['channel_name']):
                    analyzer.send_warning_message(channel['channel_id'], channel['channel_name'], dry_run=dry_run)
                    time.sleep(0.2)  # Rate limiting
            else:
                print("No channels to warn.")
            return
        elif arg == '--help':
            print("Usage: python slack_channel_analytics.py [options]")
            print("\nOptions:")
            print("  --limit N            Analyze only first N channels (useful for testing)")
            print("  --channel ID         Analyze a single channel by ID (detailed analysis)")
            print("  --join-channels      Join bot to all channels for accurate data collection")
            print("  --send-warnings      Send warning messages to channels (from saved report)")
            print("  --help               Show this help message")
            print("\nExamples:")
            print("  python slack_channel_analytics.py                      # Analyze all channels")
            print("  python slack_channel_analytics.py --limit 100          # Analyze first 100 channels")
            print("  python slack_channel_analytics.py --channel C19MR7EM9  # Analyze one channel")
            print("  python slack_channel_analytics.py --send-warnings      # Send warnings (dry run)")
            print("  python slack_channel_analytics.py --send-warnings --for-real  # Actually send warnings")
            print("\nNote: For accurate member counts and message history, the bot must be")
            print("      in the channels. Use --join-channels to add the bot to all public channels.")
            return

    analyzer = ChannelAnalyzer(token, config)

    # Handle single channel analysis
    if channel_id:
        print("\n" + "=" * 70)
        print(f"DETAILED ANALYSIS FOR CHANNEL {channel_id}")
        print("=" * 70 + "\n")

        # Create a fake channel object
        fake_channel = {'id': channel_id, 'name': channel_id}
        analysis = analyzer.analyze_channel(fake_channel)

        if analysis:
            print(f"Channel Name: {analysis['channel_name']}")
            print(f"Channel ID: {analysis['channel_id']}")
            print(f"Is Private: {analysis['is_private']}")
            print(f"Is Archived: {analysis['is_archived']}")
            print(f"Created: {analysis['created_date']}")
            print(f"Days Old: {analysis['days_old']}")
            print(f"Member Count: {analysis['member_count']}")
            print(f"Has Messages: {analysis['has_messages']}")
            print(f"Last Message Date: {analysis['last_message_date']}")
            print(f"Days Since Last Message: {analysis['days_since_last_message']}")
            print(f"Pinned Items: {analysis['pinned_count']}")
            print(f"Topic: {analysis['topic']}")
            print(f"Purpose: {analysis['purpose']}")
            print("\n" + "=" * 70)
        else:
            print("❌ Failed to analyze channel")
        return

    # Fetch and analyze
    # If a limit is set, fetch more than needed to ensure we get the specific channels
    fetch_limit = None
    if limit:
        fetch_limit = limit * 5  # Fetch more to ensure we have the specific channels

    analyzer.fetch_all_channels(limit=fetch_limit)

    # If a limit is set, trim the channels
    if limit:
        analyzer.channels = analyzer.channels[:limit]
        print(f"Analyzing {len(analyzer.channels)} channels\n")

    analyzer.analyze_all_channels()

    # Generate report
    report, categories = analyzer.generate_report()
    analyzer.print_summary(categories)

    output_config = analyzer.config.get('output', {})
    report_file = output_config.get('report_file', 'channel_analysis.json')
    csv_file = output_config.get('csv_file', 'channel_analysis.csv')
    export_csv = output_config.get('export_csv', True)

    print(f"\nReport saved to: {report_file}")
    if export_csv:
        print(f"CSV export saved to: {csv_file}")

    # Dry run - show what would be archived
    print("\n" + "=" * 70)
    print("Dry Run Mode")
    print("=" * 70)

    to_archive = categories['very_old'] + categories['never_used'] + categories['dormant']
    if to_archive:
        print(f"\nWould archive {len(to_archive)} channels:")
        for i, channel in enumerate(sorted(to_archive, key=lambda x: x['channel_name']), 1):
            analyzer.archive_channel(channel['channel_id'], channel['channel_name'], dry_run=True)
        print(f"\nTo execute cleanup, run: python slack_channel_archive.py --execute")
    else:
        print("\nNo channels eligible for cleanup.")


if __name__ == "__main__":
    main()

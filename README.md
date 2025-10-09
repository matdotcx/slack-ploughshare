# Slack Ploughshare

A professional Slack workspace analytics tool for identifying and managing inactive channels. Named after the biblical concept of beating swords into ploughshares - transforming cluttered workspaces into organised, productive environments.

## Features

- **Channel Activity Analysis** - Analyze all public channels for usage patterns
- **Configurable Thresholds** - Customise what counts as "dormant" vs "very old" channels
- **Multiple Export Formats** - JSON and CSV exports for easy analysis in spreadsheets
- **Warning Messages** - Send configurable warnings to channels before archival
- **Warning Tracking** - Track which channels have been warned to prevent duplicates
- **Reaction Monitoring** - Users can save channels by reacting to warning messages
- **Weekly Automation** - Automated weekly workflow for hands-off workspace management
- **Detailed Reporting** - View status of warned, saved, and archived channels
- **Smart Rate Limiting** - Respects Slack API rate limits with automatic retries
- **Live Progress Tracking** - Real-time progress updates during analysis
- **VPS-Friendly** - Simple cron-based automation requiring minimal resources
- **Professional Output** - Clean, well-formatted reports

## Requirements

- Python 3.7+
- Slack workspace with admin access
- Slack App with appropriate scopes
- Linux VPS (optional, for automation) - 256MB RAM minimum

## Installation

1. Clone the repository:
```bash
git clone https://github.com/matdotcx/slack-ploughshare.git
cd slack-ploughshare
```

2. Install dependencies:
```bash
pip install slack-sdk python-dotenv pyyaml
```

3. Create a Slack App:
   - Go to https://api.slack.com/apps
   - Create a new app
   - Add the following User Token Scopes:
     - `channels:read` - View basic information about public channels
     - `channels:history` - View messages in public channels
     - `users:read` - View people in the workspace
     - `chat:write` - Send messages (for warnings)
     - `reactions:read` - Check for reactions on warning messages
   - Optional: Add `groups:read` and `groups:history` for private channels (requires bot to be added to each channel)
   - Install the app to your workspace

4. Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env` and add your token:
```
SLACK_BOT_TOKEN=xoxp-your-user-token-here
```

5. Configure settings (optional):
```bash
cp slack_analytics_config.yaml.example slack_analytics_config.yaml
# Edit slack_analytics_config.yaml to customize thresholds and behavior
```

## How It Works

### Automated Weekly Workflow

Slack Ploughshare runs three jobs weekly with proper spacing to give users time to respond:

1. **Analysis & Warnings** (e.g., Monday 1 AM)
   - Scans all workspace channels
   - Identifies inactive channels (30+ days dormant, 180+ very old, or never used)
   - Sends warning messages to NEW inactive channels only
   - Records warnings with 30-day deadline in `channel_warnings.json`
   - Skips channels already warned

2. **Reaction Check** (e.g., Monday 9 AM)
   - Reviews all warned channels
   - Checks for thumbs-up reactions on warning messages
   - Marks channels as "saved" if reactions found
   - Updates warning tracker

3. **Archival** (e.g., Monday 5 PM)
   - Finds channels warned 30+ days ago
   - Excludes channels saved by reactions
   - Archives remaining inactive channels
   - Logs all actions

### Timeline Example

```
Oct 7:  Channel #old-project warned (archive date: Nov 6)
Oct 14: Reaction check - no reaction yet
Oct 21: Reaction check - user added thumbs up - Channel saved
Oct 28: Reaction check - still saved
Nov 4:  Would have been archived, but saved by reaction

Oct 7:  Channel #abandoned-temp warned (archive date: Nov 6)
Oct 14: Reaction check - no reaction
Oct 21: Reaction check - no reaction
Oct 28: Reaction check - no reaction
Nov 4:  No reaction after 30 days - ARCHIVED
```

## Usage

### Basic Analysis

Analyze all public channels:
```bash
python slack_channel_analytics.py
```

Analyze first 100 channels (for testing):
```bash
python slack_channel_analytics.py --limit 100
```

### Single Channel Analysis

Get detailed information about a specific channel:
```bash
python slack_channel_analytics.py --channel C19MR7EM9
```

### Warning Messages

Send warning messages to inactive channels (dry run):
```bash
python slack_channel_analytics.py --send-warnings
```

Actually send the warnings:
```bash
python slack_channel_analytics.py --send-warnings --for-real
```

### Automation Commands

Check warning status:
```bash
python slack_channel_analytics.py --warning-report
```

Automated workflow (for cron):
```bash
# Analyze and warn new inactive channels
python slack_channel_analytics.py --auto-warn --for-real

# Check reactions on warned channels
python slack_channel_analytics.py --check-reactions

# Archive channels past 30-day warning period
python slack_channel_analytics.py --auto-archive --for-real
```

### Help

```bash
python slack_channel_analytics.py --help
```

## VPS Deployment

### Quick Setup

1. Clone to your VPS:
```bash
ssh user@your-vps.com
git clone https://github.com/matdotcx/slack-ploughshare.git
cd slack-ploughshare
```

2. Install dependencies:
```bash
pip3 install slack-sdk python-dotenv pyyaml
```

3. Configure:
```bash
cp .env.example .env
nano .env  # Add your SLACK_BOT_TOKEN

cp slack_analytics_config.yaml.example slack_analytics_config.yaml
nano slack_analytics_config.yaml  # Customize schedules and thresholds
```

4. Test manually first:
```bash
# Dry run to see what would happen
python3 slack_channel_analytics.py --auto-warn
python3 slack_channel_analytics.py --check-reactions
python3 slack_channel_analytics.py --auto-archive

# Test for real on a small scale
python3 slack_channel_analytics.py --limit 10
python3 slack_channel_analytics.py --send-warnings --for-real
```

5. Install cron jobs:
```bash
chmod +x setup_cron.sh
./setup_cron.sh
```

6. Verify cron installation:
```bash
crontab -l
```

### Customizing Schedule

Edit `slack_analytics_config.yaml`:
```yaml
automation:
  schedule_auto_warn: "0 1 * * 1"          # Monday 1 AM
  schedule_check_reactions: "0 9 * * 1"    # Monday 9 AM
  schedule_auto_archive: "0 17 * * 1"      # Monday 5 PM
```

Change to Sundays:
```yaml
automation:
  schedule_auto_warn: "0 1 * * 0"          # Sunday 1 AM
  schedule_check_reactions: "0 9 * * 0"    # Sunday 9 AM
  schedule_auto_archive: "0 17 * * 0"      # Sunday 5 PM
```

Monthly (first day of month):
```yaml
automation:
  schedule_auto_warn: "0 1 1 * *"          # 1st, 1 AM
  schedule_check_reactions: "0 9 1 * *"    # 1st, 9 AM
  schedule_auto_archive: "0 17 1 * *"      # 1st, 5 PM
```

Then re-run:
```bash
./setup_cron.sh
```

### Disabling Automation

Edit `slack_analytics_config.yaml`:
```yaml
automation:
  enable_auto_warn: false
  enable_auto_check_reactions: false
  enable_auto_archive: false
```

Then re-run:
```bash
./setup_cron.sh
```

### Monitoring

Check logs:
```bash
tail -f logs/warnings.log
tail -f logs/reactions.log
tail -f logs/archive.log
```

View warning status:
```bash
python3 slack_channel_analytics.py --warning-report
```

## Configuration

Edit `slack_analytics_config.yaml` to customise:

### Analysis Thresholds
```yaml
analysis:
  days_dormant: 30        # Channels inactive for 30+ days
  days_very_old: 180      # Channels inactive for 180+ days
```

### Automation Settings
```yaml
automation:
  enable_auto_warn: true
  enable_auto_check_reactions: true
  enable_auto_archive: true
  schedule_auto_warn: "0 1 * * 1"           # Monday 1 AM
  schedule_check_reactions: "0 9 * * 1"     # Monday 9 AM
  schedule_auto_archive: "0 17 * * 1"       # Monday 5 PM
```

### Warning Messages
```yaml
cleanup:
  send_warning: true
  warning_days_before_archive: 30
  warning_message: |
    This channel has been inactive and is scheduled for archival.
    React with a thumbs up within 30 days to keep it active.

  # Optional: Category-specific messages
  warning_message_very_old: |
    WARNING: This channel has been inactive for over 180 days...
  warning_message_dormant: |
    NOTICE: This channel has been dormant for 30+ days...
  warning_message_never_used: |
    This channel was created but has never been used...

  # Reactions that save a channel from archival
  save_reactions: ["thumbsup", "+1", "white_check_mark"]
```

### Rate Limiting
```yaml
rate_limiting:
  delay_between_requests_ms: 100  # Delay between API calls
  smart_rate_limiting: true       # Respect Slack's rate limit headers
```

### Output Settings
```yaml
output:
  report_file: "channel_analysis.json"
  export_csv: true
  csv_file: "channel_analysis.csv"
```

## Output

The tool generates multiple files:

### JSON Report (`channel_analysis.json`)
Complete analysis with all channel data and categorizations.

### CSV Export (`channel_analysis.csv`)
Spreadsheet-friendly format with columns:
- channel_name
- channel_id
- category (active/dormant/very_old/never_used)
- member_count
- days_since_last_message
- last_message_date
- created_date
- warned_at (timestamp when warning was sent)
- archive_scheduled_for (30-day deadline)
- saved_by_reaction (true/false)
- warning_status (warned/saved/archived)
- reactions_found (thumbs up, etc.)
- topic
- purpose

Import directly into Google Sheets or Excel for further analysis!

### Warning Tracker (`channel_warnings.json`)
Persistent state tracking which channels have been warned, saved by reactions, or archived.
This prevents duplicate warnings and enables the 30-day warning period workflow.

## Channel Categories

Channels are categorized as:

- **Active** - Recent activity (within threshold)
- **Dormant** - Inactive for 30+ days (configurable)
- **Very Old** - Inactive for 180+ days (configurable)
- **Never Used** - Zero messages ever posted

## Troubleshooting

### "Missing 'groups:read' scope for private channels"
This is normal if you only want to analyze public channels. To analyze private channels, add the `groups:read` and `groups:history` scopes and ensure the bot is added to those channels.

### Rate Limiting
The tool automatically handles rate limiting with retries. Adjust `delay_between_requests_ms` in the config if you want to be more/less aggressive.

### Member Counts Show 0
Make sure your token has the `channels:read` scope and you're using `include_num_members=True` in API calls (already configured).

## Contributing

Contributions welcome! Please open an issue or PR.

## License

MIT License - See LICENSE file for details

## Credits

Built with Claude Code by @matdotcx

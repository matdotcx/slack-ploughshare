# Slack Ploughshare

A professional Slack workspace analytics tool for identifying and managing inactive channels. Named after the biblical concept of beating swords into ploughshares - transforming cluttered workspaces into organised, productive environments.

## Features

- **Channel Activity Analysis** - Analyze all public channels for usage patterns
- **Configurable Thresholds** - Customise what counts as "dormant" vs "very old" channels
- **Multiple Export Formats** - JSON and CSV exports for easy analysis in spreadsheets
- **Warning Messages** - Send configurable warnings to channels before archival
- **Smart Rate Limiting** - Respects Slack API rate limits with automatic retries
- **Live Progress Tracking** - Real-time progress updates during analysis
- **Professional Output** - Clean, well-formatted reports

## Requirements

- Python 3.7+
- Slack workspace with admin access
- Slack App with appropriate scopes

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

### Help

```bash
python slack_channel_analytics.py --help
```

## Configuration

Edit `slack_analytics_config.yaml` to customise:

### Analysis Thresholds
```yaml
analysis:
  days_dormant: 30        # Channels inactive for 30+ days
  days_very_old: 180      # Channels inactive for 180+ days
```

### Warning Messages
```yaml
cleanup:
  send_warning: true
  warning_days_before_archive: 30
  warning_message: |
    This channel has been inactive and is scheduled for archival.
    React with 👍 within 30 days to keep it active.
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

The tool generates two files:

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
- topic
- purpose

Import directly into Google Sheets or Excel for further analysis!

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

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

### Automated Workflows

Slack Ploughshare runs automated monitoring on a scheduled basis:

1. **Daily (9 AM UTC)**
   - Check reactions on warned channels
   - Update warning tracker for saved channels

2. **Weekly (Monday 9 AM UTC)**
   - Check reactions on warned channels
   - Run test warnings dry run (posts summary to Slack)
   - Run test archive dry run (posts summary to Slack)
   - Send status reminder to Slack with action items

3. **Monthly (1st of month, 9 AM UTC)**
   - Run full channel analysis (analyses all workspace channels)
   - Check reactions
   - Run test warnings and archive dry runs
   - Send comprehensive status report

All automated workflows are **read-only** - they analyze, test, and report but never execute destructive actions without manual confirmation.

### Manual Execution Workflows

These workflows require manual triggering via GitHub Actions:

**Analysis & Reporting:**
- **Manual: Run Full Channel Analysis** - Re-run analysis outside monthly schedule
- **Manual: Send Analysis Report to Slack** - Post analysis report to Slack channel
- **Manual: View Warning Tracker Status** - Console-only status check

**Testing (Dry Runs):**
- **Manual: Test Warnings (Dry Run)** - Preview what warnings would be sent
- **Manual: Test Archive (Dry Run)** - Preview what channels would be archived
- **Manual: Check Reaction Status** - Check which channels have been saved by reactions

**Execution (Requires CONFIRM):**
- **Manual: Execute - Send Warnings (CONFIRM Required)** - Actually send warning messages
- **Manual: Execute - Archive Channels (CONFIRM Required)** - Actually archive channels

### Workflow Timeline Example

```
Week 1 (Monday): Automated dry runs show #old-project would be warned
Week 1 (Tuesday): Review dry runs, run "Execute - Send Warnings" with CONFIRM
                  Channel #old-project warned (archive scheduled 30 days out)

Week 2 (Monday): Automated reaction check runs
Week 2 (Tuesday): User adds thumbs-up reaction - Channel saved

Week 3 (Monday): Automated reaction check confirms channel still saved
Week 4 (Monday): Automated reaction check confirms channel still saved

Week 5 (Monday): Automated dry run shows #old-project won't be archived (saved by reaction)

---

Week 1 (Monday): Automated dry runs show #abandoned-temp would be warned
Week 1 (Tuesday): Review dry runs, run "Execute - Send Warnings" with CONFIRM
                  Channel #abandoned-temp warned (archive scheduled 30 days out)

Week 2-5 (Monday): Automated checks find no reactions
Week 5 (Monday): Automated dry run shows #abandoned-temp ready for archival
Week 5 (Tuesday): Review dry runs, run "Execute - Archive Channels" with CONFIRM
                  Channel #abandoned-temp archived
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

## Deployment Options

You can run Slack Ploughshare in two ways:

1. **GitHub Actions** (Recommended) - Free, managed, no infrastructure needed
2. **VPS/Server** - Self-hosted with cron jobs

---

## GitHub Actions Deployment (Recommended)

**[📖 Full GitHub Actions Setup Guide](.github/GITHUB_ACTIONS_SETUP.md)**

### Why GitHub Actions?

- **Free** - 2,000 minutes/month on free tier
- **Managed** - No server to maintain
- **Secrets Management** - Built-in secure token storage
- **Artifacts** - Automatic state persistence between runs
- **Manual Triggers** - Test anytime via UI
- **Logs** - Full execution history in GitHub

### Quick Setup

1. **Fork or clone this repository to your GitHub account**

2. **Add your Slack token as a secret:**
   - Go to your repository on GitHub
   - Settings > Secrets and variables > Actions
   - Click "New repository secret"
   - Name: `SLACK_BOT_TOKEN`
   - Value: Your Slack bot token (starts with `xoxb-`)
   - Click "Add secret"

3. **Customize schedule (optional):**
   - Edit `.github/workflows/slack-ploughshare-automation.yml`
   - Modify the cron schedules:
     ```yaml
     on:
       schedule:
         - cron: '0 1 * * 1'   # Auto-warn: Monday 1 AM UTC
         - cron: '0 9 * * 1'   # Check reactions: Monday 9 AM UTC
         - cron: '0 17 * * 1'  # Auto-archive: Monday 5 PM UTC
     ```
   - Convert to your timezone (UTC times shown)
   - Commit and push changes

4. **Customize configuration (optional):**
   - Copy `slack_analytics_config.yaml.example` to `slack_analytics_config.yaml`
   - Customize thresholds, messages, etc.
   - Commit and push

5. **Enable GitHub Actions:**
   - Go to Actions tab in your repository
   - Click "I understand my workflows, go ahead and enable them"

6. **Test with manual trigger:**
   - Go to Actions tab
   - Select "Slack Ploughshare Weekly Automation"
   - Click "Run workflow"
   - Choose command: `warning-report`
   - Dry run: `true`
   - Click "Run workflow"

### How It Works

**Automated Monitoring:**
GitHub Actions runs scheduled workflows automatically:
- **Daily (9 AM UTC)** - Check reactions on warned channels
- **Weekly (Monday 9 AM UTC)** - Full status check with dry run reports posted to Slack
- **Monthly (1st, 9 AM UTC)** - Complete workspace analysis

**Available Workflows:**

*Automated:*
- **Automated: Scheduled Monitoring & Reminders** - Runs daily/weekly/monthly checks

*Manual - Analysis & Reporting:*
- **Manual: Run Full Channel Analysis** - Full workspace scan
- **Manual: Send Analysis Report to Slack** - Post analysis to Slack
- **Manual: View Warning Tracker Status** - Console status check

*Manual - Testing (Safe):*
- **Manual: Test Warnings (Dry Run)** - Preview warnings (posts to Slack)
- **Manual: Test Archive (Dry Run)** - Preview archival (posts to Slack)
- **Manual: Check Reaction Status** - Check saved channels

*Manual - Execution (Destructive):*
- **Manual: Execute - Send Warnings (CONFIRM Required)** - Actually send warnings
- **Manual: Execute - Archive Channels (CONFIRM Required)** - Actually archive channels

**State Persistence:**
- State files tracked in git repository
- GitHub Actions commits state updates after each run
- Warning tracker maintains 30-day warning periods
- Each workspace maintains its own state

**Safety Features:**
- Automated workflows are read-only (analyze and report only)
- Execute workflows require typing "CONFIRM"
- Dry runs post results to Slack before execution
- Full execution logs and summaries
- State history tracked in git for audit trail

### Monitoring

View execution logs:
- Go to Actions tab
- Click on workflow run
- Expand steps to see detailed logs
- Download artifacts for full analysis

Check summary:
- Each run shows summary with warning tracker stats
- See how many channels are tracked, warned, saved, archived

### Timezone Conversion

GitHub Actions uses UTC. Convert your desired times:

**Example: Want Monday 9 AM PST (UTC-8)?**
- PST 9 AM = UTC 5 PM
- Cron: `0 17 * * 1`

**Example: Want Monday 1 PM CET (UTC+1)?**
- CET 1 PM = UTC 12 PM
- Cron: `0 12 * * 1`

Use [crontab.guru](https://crontab.guru) for help with cron expressions.

### Costs

GitHub Actions free tier:
- 2,000 minutes/month
- Each run takes ~5-10 minutes (depends on workspace size)
- Weekly schedule = ~12 runs/month = ~120 minutes/month
- Well within free tier

For large workspaces (1000+ channels):
- Runs may take 15-30 minutes
- Still ~360 minutes/month = within free tier

---

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
  days_dormant: 380       # Channels inactive for 380+ days (12+ months)
  days_very_old: 550      # Channels inactive for 550+ days (18 months)
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
- **Dormant** - Inactive for 380+ days / 12+ months (configurable)
- **Very Old** - Inactive for 550+ days / 18 months (configurable)
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

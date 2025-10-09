# GitHub Actions Setup Guide

Run Slack Ploughshare automatically using GitHub Actions - no server required!

## Prerequisites

1. A GitHub account
2. A Slack workspace with admin access
3. A Slack bot token with these scopes:
   - `channels:read`
   - `channels:history`
   - `users:read`
   - `chat:write`
   - `reactions:read`

## Step-by-Step Setup

### 1. Get Your Repository

**Option A: Fork this repository**
- Click "Fork" button at the top of this page
- This creates your own copy under your GitHub account

**Option B: Clone to your account**
```bash
git clone https://github.com/matdotcx/slack-ploughshare.git
cd slack-ploughshare
# Create your own repo on GitHub, then:
git remote set-url origin https://github.com/YOUR_USERNAME/slack-ploughshare.git
git push -u origin main
```

### 2. Add Slack Token as Secret

1. Go to your repository on GitHub
2. Click **Settings** (top menu)
3. In the left sidebar, click **Secrets and variables** > **Actions**
4. Click **New repository secret**
5. Fill in:
   - **Name:** `SLACK_BOT_TOKEN`
   - **Secret:** Your Slack bot token (starts with `xoxb-`)
6. Click **Add secret**

### 3. Customize Configuration (Optional)

Create `slack_analytics_config.yaml` in your repo:

```bash
cp slack_analytics_config.yaml.example slack_analytics_config.yaml
```

Edit the file to customize:
- Warning message text
- Days until dormant/very old
- Save reactions
- Category-specific messages

Commit and push:
```bash
git add slack_analytics_config.yaml
git commit -m "Add custom configuration"
git push
```

### 4. Customize Schedule (Optional)

Edit `.github/workflows/slack-ploughshare-automation.yml`:

```yaml
on:
  schedule:
    # Change these times (UTC)
    - cron: '0 1 * * 1'   # Auto-warn
    - cron: '0 9 * * 1'   # Check reactions
    - cron: '0 17 * * 1'  # Auto-archive
```

**Timezone Conversion Examples:**

| Your Time | UTC Equivalent | Cron |
|-----------|---------------|------|
| Mon 9 AM PST (UTC-8) | Mon 5 PM UTC | `0 17 * * 1` |
| Mon 9 AM EST (UTC-5) | Mon 2 PM UTC | `0 14 * * 1` |
| Mon 9 AM CET (UTC+1) | Mon 8 AM UTC | `0 8 * * 1` |
| Mon 9 AM JST (UTC+9) | Mon 12 AM UTC | `0 0 * * 1` |

Commit and push:
```bash
git add .github/workflows/slack-ploughshare-automation.yml
git commit -m "Customize schedule for my timezone"
git push
```

### 5. Enable GitHub Actions

1. Go to **Actions** tab in your repository
2. If you see a banner about workflows, click **"I understand my workflows, go ahead and enable them"**
3. You should now see "Slack Ploughshare Weekly Automation" workflow

### 6. Test It Out

**Manual Test Run:**

1. Go to **Actions** tab
2. Click **"Slack Ploughshare Weekly Automation"** in the left sidebar
3. Click **"Run workflow"** button (top right)
4. Fill in the form:
   - **Command:** `warning-report`
   - **Dry run mode:** `true`
5. Click **"Run workflow"**
6. Click on the workflow run to see progress
7. Check the summary for statistics

**Test with actual warning (safe):**

1. Run workflow again
2. **Command:** `auto-warn`
3. **Dry run mode:** `true` (keeps it safe)
4. Review the logs to see what would happen

**When ready to go live:**

1. Run workflow
2. **Command:** `auto-warn`
3. **Dry run mode:** `false` (will actually send warnings)

## How State is Maintained

GitHub Actions is stateless by default, but we use **Artifacts** to persist data:

### Warning Tracker Artifact
- **File:** `channel_warnings.json`
- **Retention:** 90 days
- **Contains:** Which channels are warned, saved, archived
- Downloaded at start of each run
- Uploaded at end of each run

### Channel Analysis Artifact
- **Files:** `channel_analysis.json`, `channel_analysis.csv`
- **Retention:** 30 days
- **Contains:** Latest channel analysis results
- Optional - mainly for your reference

### Logs Artifact
- **Files:** All log files
- **Retention:** 14 days
- **Contains:** Execution logs for debugging

## Monitoring

### View Execution Logs

1. Go to **Actions** tab
2. Click on a workflow run
3. Expand any step to see detailed logs
4. Download artifacts at the bottom for full files

### Check Summary

Each run shows a summary with:
- Command executed
- Dry run or real execution
- Timestamp
- Warning tracker statistics (total, warned, saved, archived)

### Download Data

1. Go to completed workflow run
2. Scroll to **Artifacts** section at bottom
3. Download:
   - `warning-tracker` - Current state
   - `channel-analysis` - Latest analysis
   - `logs-XXX` - Execution logs

## Troubleshooting

### Workflow not running on schedule

**Check:**
1. GitHub Actions are enabled (Actions tab)
2. Repository is not archived
3. You've had recent activity in the repo (push something if not)
4. Schedule syntax is correct in YAML

**Note:** GitHub may delay scheduled workflows by up to 10 minutes during high load.

### "Error: SLACK_BOT_TOKEN not found"

**Fix:**
1. Go to Settings > Secrets and variables > Actions
2. Verify `SLACK_BOT_TOKEN` secret exists
3. Check the name is exactly `SLACK_BOT_TOKEN` (case-sensitive)
4. Re-add the secret if needed

### No warning tracker artifact found

**This is normal on first run!**
- First run creates the `channel_warnings.json`
- Subsequent runs will download it automatically
- If you need to reset, delete the artifact in the Actions tab

### Want to reset everything

1. Go to Actions tab
2. Click on "Slack Ploughshare Weekly Automation"
3. Find and delete the `warning-tracker` artifact
4. Next run will start fresh

## Cost Estimate

GitHub Actions free tier: **2,000 minutes/month**

Typical usage:
- Small workspace (50 channels): ~2 minutes/run
- Medium workspace (500 channels): ~5 minutes/run
- Large workspace (2000 channels): ~15 minutes/run

Weekly schedule (3 runs/week):
- Small: ~24 minutes/month
- Medium: ~60 minutes/month
- Large: ~180 minutes/month

**All well within the free tier!**

For workspaces over 5,000 channels, consider VPS deployment instead.

## Next Steps

Once everything is working:

1. **Review warning report weekly:**
   - Run manual workflow with `warning-report` command
   - Check which channels are being tracked

2. **Monitor first warning cycle:**
   - Watch the first 30-day period closely
   - Ensure users understand the thumbs-up reaction
   - Adjust messages if needed

3. **Fine-tune thresholds:**
   - Edit `slack_analytics_config.yaml`
   - Adjust `days_dormant` and `days_very_old`
   - Commit and push changes

4. **Set and forget:**
   - Once tuned, it runs automatically
   - Check in monthly via warning report
   - Review archived channels periodically

## Support

For issues or questions:
- Check the logs in Actions tab
- Review the main README.md
- Open an issue on GitHub

Happy channel cleanup!

#!/bin/bash
# Slack Ploughshare - Cron Setup
# Installs weekly jobs with proper spacing

INSTALL_DIR=$(pwd)
CONFIG_FILE="slack_analytics_config.yaml"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "[ERROR] $CONFIG_FILE not found"
    echo "Please copy slack_analytics_config.yaml.example to slack_analytics_config.yaml"
    exit 1
fi

# Read schedules from config
AUTO_WARN_SCHEDULE=$(python3 -c "import yaml; c=yaml.safe_load(open('$CONFIG_FILE')); print(c.get('automation',{}).get('schedule_auto_warn','0 1 * * 1'))" 2>/dev/null || echo "0 1 * * 1")
CHECK_REACTIONS_SCHEDULE=$(python3 -c "import yaml; c=yaml.safe_load(open('$CONFIG_FILE')); print(c.get('automation',{}).get('schedule_check_reactions','0 9 * * 1'))" 2>/dev/null || echo "0 9 * * 1")
AUTO_ARCHIVE_SCHEDULE=$(python3 -c "import yaml; c=yaml.safe_load(open('$CONFIG_FILE')); print(c.get('automation',{}).get('schedule_auto_archive','0 17 * * 1'))" 2>/dev/null || echo "0 17 * * 1")

ENABLE_WARN=$(python3 -c "import yaml; c=yaml.safe_load(open('$CONFIG_FILE')); print(str(c.get('automation',{}).get('enable_auto_warn',True)))" 2>/dev/null || echo "True")
ENABLE_REACTIONS=$(python3 -c "import yaml; c=yaml.safe_load(open('$CONFIG_FILE')); print(str(c.get('automation',{}).get('enable_auto_check_reactions',True)))" 2>/dev/null || echo "True")
ENABLE_ARCHIVE=$(python3 -c "import yaml; c=yaml.safe_load(open('$CONFIG_FILE')); print(str(c.get('automation',{}).get('enable_auto_archive',True)))" 2>/dev/null || echo "True")

mkdir -p logs

echo "[INFO] Installing Slack Ploughshare cron jobs"
echo ""
echo "Schedule:"
echo "  Auto-warn:        $AUTO_WARN_SCHEDULE (enabled: $ENABLE_WARN)"
echo "  Check reactions:  $CHECK_REACTIONS_SCHEDULE (enabled: $ENABLE_REACTIONS)"
echo "  Auto-archive:     $AUTO_ARCHIVE_SCHEDULE (enabled: $ENABLE_ARCHIVE)"
echo ""
echo "Timeline:"
echo "  - Warnings sent to new inactive channels"
echo "  - 30-day response period for users to react"
echo "  - Reaction checks run weekly"
echo "  - Archival happens 30+ days after warning"
echo ""

# Remove existing jobs
crontab -l 2>/dev/null | grep -v "Slack Ploughshare" | grep -v "slack_channel_analytics.py" | crontab -

# Add header
(crontab -l 2>/dev/null; echo "# Slack Ploughshare - Weekly automation") | crontab -

# Find python3 path
PYTHON_PATH=$(which python3)

# Add enabled jobs
if [ "$ENABLE_WARN" = "True" ]; then
    (crontab -l 2>/dev/null; echo "$AUTO_WARN_SCHEDULE cd $INSTALL_DIR && $PYTHON_PATH slack_channel_analytics.py --auto-warn --for-real >> logs/warnings.log 2>&1") | crontab -
fi

if [ "$ENABLE_REACTIONS" = "True" ]; then
    (crontab -l 2>/dev/null; echo "$CHECK_REACTIONS_SCHEDULE cd $INSTALL_DIR && $PYTHON_PATH slack_channel_analytics.py --check-reactions >> logs/reactions.log 2>&1") | crontab -
fi

if [ "$ENABLE_ARCHIVE" = "True" ]; then
    (crontab -l 2>/dev/null; echo "$AUTO_ARCHIVE_SCHEDULE cd $INSTALL_DIR && $PYTHON_PATH slack_channel_analytics.py --auto-archive --for-real >> logs/archive.log 2>&1") | crontab -
fi

echo "[SUCCESS] Cron jobs installed"
echo ""
echo "Verify installation: crontab -l"
echo "Modify schedule: edit slack_analytics_config.yaml and re-run ./setup_cron.sh"
echo "View logs: tail -f logs/*.log"
echo ""
echo "To test manually before waiting for cron:"
echo "  python3 slack_channel_analytics.py --auto-warn"
echo "  python3 slack_channel_analytics.py --check-reactions"
echo "  python3 slack_channel_analytics.py --auto-archive"

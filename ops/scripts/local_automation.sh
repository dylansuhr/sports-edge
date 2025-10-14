#!/bin/bash
# Local automation script - run via cron
# Add to crontab: */20 * * * * /path/to/local_automation.sh

PROJECT_DIR="/Users/dylansuhr/Developer/dylan_suhr/web_apps/sports-edge"
cd "$PROJECT_DIR" || exit 1

# Activate virtual environment
source .venv/bin/activate

# Log file
LOG_FILE="$PROJECT_DIR/logs/automation.log"
mkdir -p "$PROJECT_DIR/logs"

echo "[$(date)] Starting automation cycle..." >> "$LOG_FILE"

# Fetch odds (NFL-only until edge validated)
echo "[$(date)] Fetching odds..." >> "$LOG_FILE"
.venv/bin/python ops/scripts/odds_etl_v2.py --leagues nfl >> "$LOG_FILE" 2>&1

# Generate signals (NFL-only)
echo "[$(date)] Generating signals..." >> "$LOG_FILE"
.venv/bin/python ops/scripts/generate_signals_v2.py --leagues nfl >> "$LOG_FILE" 2>&1

# Capture closing lines (NFL-only, only during game windows)
echo "[$(date)] Capturing closing lines..." >> "$LOG_FILE"
.venv/bin/python ops/scripts/capture_closing_lines.py --leagues nfl --minutes-ahead 30 >> "$LOG_FILE" 2>&1

echo "[$(date)] Automation cycle complete." >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"

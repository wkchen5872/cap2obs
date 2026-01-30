#!/bin/bash
# Example automation script for Cap2Obs
# This can be used as a cron job or systemd timer

# Configuration
BACKUP_DIR="/path/to/capacities/backups"
OBSIDIAN_VAULT="/path/to/obsidian/vault"
LOG_FILE="/var/log/cap2obs.log"
KEEP_DAYS=7

# Run Cap2Obs
/usr/local/bin/cap2obs \
  --backup-dir "$BACKUP_DIR" \
  --obsidian-vault "$OBSIDIAN_VAULT" \
  --log-file "$LOG_FILE" \
  --keep-days "$KEEP_DAYS"

# Capture exit code
EXIT_CODE=$?

# Optional: Send notification based on exit code
if [ $EXIT_CODE -eq 0 ]; then
    # Successful sync
    # echo "Cap2Obs sync successful" | mail -s "Sync Success" user@example.com
    exit 0
else
    # Failed sync - send alert
    echo "Cap2Obs sync failed with exit code $EXIT_CODE. Check $LOG_FILE for details." | mail -s "Sync Failed" user@example.com
    exit $EXIT_CODE
fi

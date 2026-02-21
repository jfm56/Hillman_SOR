#!/bin/bash
# Setup automatic daily backups via cron
# Run this script once on the server to enable automatic backups

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup.sh"

# Make scripts executable
chmod +x "$SCRIPT_DIR/backup.sh"
chmod +x "$SCRIPT_DIR/restore.sh"

# Add cron job for daily backup at 6 PM (end of business day)
CRON_JOB="0 18 * * * $BACKUP_SCRIPT >> /var/log/sor-backup.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "backup.sh"; then
    echo "Backup cron job already exists."
else
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "Added daily backup cron job (runs at 6 PM)"
fi

echo ""
echo "Backup configuration:"
echo "  - Script: $BACKUP_SCRIPT"
echo "  - Schedule: Daily at 6:00 PM"
echo "  - Log: /var/log/sor-backup.log"
echo "  - Backups kept: 30 days"
echo ""
echo "To run a backup now:"
echo "  $BACKUP_SCRIPT"
echo ""
echo "To view scheduled cron jobs:"
echo "  crontab -l"

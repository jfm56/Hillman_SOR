#!/bin/bash
# Database Backup Script for SOR AI System
# Backs up PostgreSQL database to timestamped SQL files

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/home/jim/sor-ai-system/backups}"
CONTAINER_NAME="sor_postgres"
DB_NAME="${POSTGRES_DB:-sor_ai}"
DB_USER="${POSTGRES_USER:-postgres}"
KEEP_DAYS=30  # Keep backups for 30 days

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/sor_ai_backup_$TIMESTAMP.sql"

echo "Starting backup at $(date)"
echo "Backup file: $BACKUP_FILE"

# Create backup using pg_dump inside the container
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE"

# Compress the backup
gzip "$BACKUP_FILE"
BACKUP_FILE="$BACKUP_FILE.gz"

# Get file size
SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "Backup complete: $BACKUP_FILE ($SIZE)"

# Remove old backups
echo "Removing backups older than $KEEP_DAYS days..."
find "$BACKUP_DIR" -name "sor_ai_backup_*.sql.gz" -mtime +$KEEP_DAYS -delete

# List current backups
echo ""
echo "Current backups:"
ls -lh "$BACKUP_DIR"/sor_ai_backup_*.sql.gz 2>/dev/null || echo "No backups found"

echo ""
echo "Backup completed successfully at $(date)"

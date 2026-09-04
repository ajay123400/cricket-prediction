# Backup Guide

## What to back up
1. `cricket_predictions.db` (SQLite database)
2. `static/uploads/` (featured images)

## Daily automated backup (Linux/VPS via cron)

Create `/opt/cricket_backup.sh`:

```bash
#!/bin/bash
set -e
APP_DIR="/path/to/CricketPrediction"
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"
sqlite3 "$APP_DIR/cricket_predictions.db" ".backup $BACKUP_DIR/db_$DATE.db"
tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" -C "$APP_DIR/static" uploads

# keep last 14 days
find "$BACKUP_DIR" -name "db_*.db" -mtime +14 -delete
find "$BACKUP_DIR" -name "uploads_*.tar.gz" -mtime +14 -delete
```

```bash
chmod +x /opt/cricket_backup.sh
crontab -e
# add: run daily at 2:30 AM
30 2 * * * /opt/cricket_backup.sh >> /var/log/cricket_backup.log 2>&1
```

## Windows Task Scheduler equivalent

Create `backup.ps1`:

```powershell
$AppDir = "E:\CricketPrediction"
$BackupDir = "E:\CricketPrediction\backups"
$Date = Get-Date -Format "yyyyMMdd_HHmmss"
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
Copy-Item "$AppDir\cricket_predictions.db" "$BackupDir\db_$Date.db"
Compress-Archive -Path "$AppDir\static\uploads" -DestinationPath "$BackupDir\uploads_$Date.zip"
```

Schedule it daily with Task Scheduler (`Create Basic Task` → Daily → action: run
`powershell.exe -File E:\CricketPrediction\backup.ps1`).

## Restore

```bash
cp backups/db_YYYYMMDD_HHMMSS.db cricket_predictions.db
tar -xzf backups/uploads_YYYYMMDD_HHMMSS.tar.gz -C static/
```

Restart the app (gunicorn/service) after restoring.

# Cap2Obs Smart Sync

Automatic synchronization tool for Capacities backups to Obsidian vaults.

## Features

- **Smart Sync**: Hash-based content comparison to minimize file changes
- **Flexible Source Selection**: Auto-select, date-based, or explicit file selection
- **Dry-Run Mode**: Preview changes before applying
- **Automation-Ready**: Proper exit codes for cron/scheduled tasks
- **Clean Logging**: Structured logs to console or file

## Installation

### Requirements
- Python 3.10 or higher
- macOS or Linux

### Install from source
```bash
git clone <repository-url>
cd Cap2Obs
pip install -e .
```

## Usage

### Basic Sync
```bash
cap2obs --backup-dir /path/to/backups --obsidian-vault /path/to/vault
```

### With Date Selection
```bash
cap2obs --backup-dir /path/to/backups --obsidian-vault /path/to/vault --date 2026-01-30
```

### Dry-Run Mode
```bash
cap2obs --backup-dir /path/to/backups --obsidian-vault /path/to/vault --dry-run
```

### With Logging
```bash
cap2obs --backup-dir /path/to/backups --obsidian-vault /path/to/vault --log-file /var/log/cap2obs.log
```

### Auto-Cleanup Old Backups
```bash
cap2obs --backup-dir /path/to/backups --obsidian-vault /path/to/vault --keep-days 7
```

## CLI Arguments

### Required
- `--backup-dir PATH` - Directory containing Capacities backup ZIP files
- `--obsidian-vault PATH` - Target Obsidian vault directory

### Optional
- `--date YYYY-MM-DD` - Sync specific backup date (auto-selects latest if multiple)
- `--file FILENAME` - Sync specific backup file (overrides --date)
- `--dry-run` - Preview changes without applying them
- `--log-file PATH` - Write detailed logs to file
- `--keep-days N` - Delete backups older than N days after successful sync

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Backup directory not found |
| 2 | No matching backup file found |
| 3 | Obsidian vault path invalid |
| 4 | ZIP extraction failed |
| 5 | Permission denied |
| 6 | Unexpected sync error |

## Automation

### Daily Cron Job (1:00 PM)
```bash
0 13 * * * /usr/local/bin/cap2obs --backup-dir /data/backups --obsidian-vault /home/user/vault --log-file /var/log/cap2obs.log
```

### With Auto-Cleanup (Keep 7 Days)
```bash
0 13 * * * /usr/local/bin/cap2obs --backup-dir /data/backups --obsidian-vault /home/user/vault --keep-days 7 --log-file /var/log/cap2obs.log
```

## How It Works

1. **File Selection**: Finds the most recent Capacities backup ZIP
2. **Extraction**: Unzips to temporary workspace (`.temp_cap2obs/`)
3. **Hash Comparison**: Computes content hashes for all files
4. **Smart Sync**:
   - **ADD**: New files in backup
   - **UPDATE**: Files with different content hash
   - **SKIP**: Files with identical hash (preserves timestamp)
   - **DELETE**: Files removed from backup
5. **Cleanup**: Removes temporary files

## Development

### Run Tests
```bash
pytest tests/
```

### Run with Coverage
```bash
pytest --cov=cap2obs tests/
```

## License

[Add your license here]

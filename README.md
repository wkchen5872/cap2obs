# Cap2Obs Smart Sync

Automatic synchronization tool for Capacities backups to Obsidian vaults.

## Features

- **Multi-Vault Support**: Automatically detects and syncs multiple vaults in a single backup
- **Smart Sync**: Hash-based content comparison to minimize file changes
- **Scope Protection**: Delete operations are strictly limited to each vault's scope
- **Flexible Source Selection**: Auto-select, date-based, or explicit file selection
- **Dry-Run Mode**: Preview changes before applying
- **Automation-Ready**: Proper exit codes for cron/scheduled tasks
- **Clean Logging**: Per-vault progress with aggregate summaries

## Installation

### Option 1: Development Install (Recommended for easy updates)
Clone the repository and install in editable mode:
```bash
git clone <repository-url>
cd Cap2Obs
pip install -e .
```
This requires your Python environment to be active when running the command.

### Option 2: Build Standalone Binary (Recommended for Automation)
Create a standalone executable that works without an active Python environment (perfect for cron jobs).

1. Build the binary using the provided script:
   ```bash
   make build
   # OR direct script: ./scripts/build.sh
   ```

2. Install to your system path:
   ```bash
   sudo cp dist/cap2obs /usr/local/bin/
   ```

Now you can run `cap2obs` from anywhere.

### Option 3: Using pipx
If you use `pipx` to manage CLI tools:
```bash
pipx install .
```

## Usage

### Basic Sync (Multi-Vault)
```bash
cap2obs --backup-dir /path/to/backups --obsidian-root /path/to/obsidian
```

This will:
1. Extract the newest Capacities backup
2. Detect all vaults (Work, Personal, etc.)
3. Sync each vault to the corresponding folder in `--obsidian-root`

### With Date Selection
```bash
cap2obs --backup-dir /path/to/backups --obsidian-root /path/to/obsidian --date 2026-01-30
```

### Dry-Run Mode
```bash
cap2obs --backup-dir /path/to/backups --obsidian-root /path/to/obsidian --dry-run
```

### With Logging
```bash
cap2obs --backup-dir /path/to/backups --obsidian-root /path/to/obsidian --log-file /var/log/cap2obs.log
```

### Auto-Cleanup Old Backups
```bash
cap2obs --backup-dir /path/to/backups --obsidian-root /path/to/obsidian --keep-days 7
```

## CLI Arguments

### Required
- `--backup-dir PATH` - Directory containing Capacities backup ZIP files
- `--obsidian-root PATH` - Root directory containing Obsidian vault folders

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
| 3 | Obsidian root path invalid |
| 4 | ZIP extraction failed |
| 5 | Permission denied |
| 6 | Unexpected sync error (or partial failure) |

## Multi-Vault Behavior

### Backup Structure Detection

Cap2Obs automatically detects two backup structures:

**Nested (Multi-Vault):**
```
Capacities (2026-01-30)/
├── Work/
└── Personal/
```

**Flat (Single Vault):**
```
Work/
└── notes/
```

### Scope Protection

Each vault is synced independently. Files in other vaults are never affected:

- Backup contains: `Work`, `Personal`
- Obsidian root contains: `Work`, `Personal`, `Family`
- Result: `Work` and `Personal` synced; `Family` is **untouched**

### 筆記對應關係

- Capacities 的 **Space** = Obsidian 的 **Vault**
- Capacities 的 **Object** 在匯出後會成為 Obsidian 中的**子資料夾**
  - 例如：Space 名稱為 `test`，則會產生 `test/` 目錄
  - Object 「Project」會在底下產生 `test/Project/` 子目錄

### 排除規則 (不刪除或覆蓋)

為了保護重要設定與文件，以下內容不會被同步規則刪除或覆蓋：

**隱藏檔案或目錄：**
* `.obsidian/`: 存放 Obsidian 的插件、佈景主題及工作區設定。
* `.smart-env/`: 存放 AI 輔助插件（如 Smart Connections）的上下文、聊天紀錄與補全資料。
* `.agents/`、`.claude`、`.gemini/`、`.github`: AI Agent 的 skill 與設定。
* `.git`: git 的資料。

**重要文件：**
* `README.md`
* `AGENTS.md`
* `CLAUDE.md`

### Migration from `--obsidian-vault`

The `--obsidian-vault` parameter is deprecated but still works:

```bash
# Old (deprecated, shows warning)
cap2obs --backup-dir /backups --obsidian-vault /obsidian

# New (recommended)
cap2obs --backup-dir /backups --obsidian-root /obsidian
```

## Automation

### Daily Cron Job (1:00 PM)
```bash
0 13 * * * /usr/local/bin/cap2obs --backup-dir /data/backups --obsidian-root /home/user/obsidian --log-file /var/log/cap2obs.log
```

### With Auto-Cleanup (Keep 7 Days)
```bash
0 13 * * * /usr/local/bin/cap2obs --backup-dir /data/backups --obsidian-root /home/user/obsidian --keep-days 7 --log-file /var/log/cap2obs.log
```

## macOS 額外設定

### 1. 授予 cron 完整磁碟存取權限

系統偏好設定 → 安全性與隱私權 → 隱私權 → 完整磁碟取用權限 → 新增 `/usr/sbin/cron`

### 2. 確認日誌目錄權限

```bash
sudo mkdir -p /var/log
sudo chmod 755 /var/log
```

或改用使用者目錄：

```bash
--log-file ~/Library/Logs/cap2obs_day.log
```
## How It Works

1. **File Selection**: Finds the most recent Capacities backup ZIP
2. **Extraction**: Unzips to temporary workspace (`.temp_cap2obs/`)
3. **Vault Detection**: Identifies vault folders in backup
4. **Per-Vault Sync**:
   - **ADD**: New files in backup
   - **UPDATE**: Files with different content hash
   - **SKIP**: Files with identical hash (preserves timestamp)
   - **DELETE**: Files removed from backup (within vault scope only)
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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

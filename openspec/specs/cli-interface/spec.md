# cli-interface Specification

## Purpose
TBD - created by archiving change implement-cap2obs-sync. Update Purpose after archive.
## Requirements
### Requirement: Command-line argument parsing

The tool SHALL expose a command-line interface accepting the following arguments.

#### Scenario: User specifies backup directory and target root

**Given** the user has Capacities backups in `/data/backups`  
**And** their Obsidian root is located at `/home/user/obsidian`  
**When** they run `cap2obs --backup-dir /data/backups --obsidian-root /home/user/obsidian`  
**Then** the tool SHALL validate both paths exist  
**And** proceed with multi-vault sync operation using these paths

---

#### Scenario: Backwards compatibility with deprecated parameter

**Given** the user has an existing script using `--obsidian-vault`  
**When** they run `cap2obs --backup-dir /data/backups --obsidian-vault /obsidian`  
**Then** the tool SHALL accept the parameter as an alias for `--obsidian-root`  
**And** SHALL log a deprecation warning: `[WARN] --obsidian-vault is deprecated, use --obsidian-root instead`  
**And** SHALL proceed with synchronization normally

---

#### Scenario: Help text reflects new parameter name

**Given** the user runs `cap2obs --help`  
**When** the help text is displayed  
**Then** it SHALL show `--obsidian-root PATH` as the required parameter  
**And** SHALL describe it as "Root directory containing Obsidian vault folders"  
**And** SHALL NOT show the deprecated `--obsidian-vault` parameter

---

#### Scenario: User specifies explicit backup file

**Given** multiple backup files exist in the backup directory  
**When** the user runs `cap2obs --backup-dir /dfs/backups --obsidian-root /obsidian --file "Capacities (2026-01-30).zip"`  
**Then** the tool SHALL use that specific file  
**And** SHALL NOT search for other files

---

#### Scenario: User specifies date-based selection

**Given** multiple backups from the same date exist  
**When** the user runs `cap2obs --backup-dir /dfs/backups --obsidian-root /obsidian --date 2026-01-30`  
**Then** the tool SHALL filter files matching `Capacities (2026-01-30 *.zip)` pattern  
**And** SHALL select the file with the latest timestamp

---

#### Scenario: Automatic backup selection

**Given** no `--file` or `--date` argument is provided  
**When** the user runs `cap2obs --backup-dir /dfs/backups --obsidian-root /obsidian`  
**Then** the tool SHALL scan all files matching `Capacities (YYYY-MM-DD HH-mm-ss).zip`  
**And** SHALL select the file with the most recent date and time

### Requirement: Dry-run preview mode

The tool SHALL support a `--dry-run` flag that previews changes without applying them.

#### Scenario: Dry-run mode execution

**Given** the user wants to preview changes  
**When** they run `cap2obs --backup-dir /data/backups --obsidian-vault /vault --dry-run`  
**Then** the tool SHALL extract and compare files  
**And** SHALL output all planned operations with `[DRY-RUN]` prefix  
**And** SHALL NOT create, modify, or delete any files in the target vault  
**And** SHALL exit with code 0 on successful preview

---

### Requirement: Logging configuration

The tool SHALL support optional log file output via `--log-file` argument.

#### Scenario: Console-only logging (default)

**Given** no `--log-file` argument is provided  
**When** the tool executes  
**Then** all log messages SHALL be written to stdout/stderr only

---

#### Scenario: File-based logging

**Given** the user specifies `--log-file /var/log/cap2obs.log`  
**When** the tool executes  
**Then** detailed logs SHALL be written to the specified file  
**And** concise progress SHALL still be shown on console

---

### Requirement: Old backup cleanup

The tool SHALL support optional automatic cleanup of old backups via `--keep-days N`.

#### Scenario: Automatic cleanup after sync

**Given** the user specifies `--keep-days 7`  
**And** a successful sync has completed  
**When** the tool scans the backup directory  
**Then** it SHALL delete ZIP files older than 7 days  
**And** SHALL log each deletion

---

#### Scenario: No cleanup by default

**Given** no `--keep-days` argument is provided  
**When** sync completes successfully  
**Then** the tool SHALL NOT delete any backup files

---

### Requirement: Exit code specification

The tool SHALL exit with standardized status codes for automation integration.

#### Scenario: Target root path invalid

**Given** the `--obsidian-root` (or `--obsidian-vault`) path does not exist  
**When** the tool validates arguments  
**Then** it SHALL exit with code `3`


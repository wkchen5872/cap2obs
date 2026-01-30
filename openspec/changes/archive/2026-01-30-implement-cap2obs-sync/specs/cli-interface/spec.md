# Spec: CLI Interface

## ADDED Requirements

### Requirement: Command-line argument parsing

The tool SHALL expose a command-line interface accepting the following arguments.

#### Scenario: User specifies backup directory and target vault

**Given** the user has Capacities backups in `/data/backups`  
**And** their Obsidian vault is located at `/home/user/vault`  
**When** they run `cap2obs --backup-dir /data/backups --obsidian-vault /home/user/vault`  
**Then** the tool SHALL validate both paths exist  
**And** proceed with sync operation using these paths

---

#### Scenario: User specifies explicit backup file

**Given** multiple backup files exist in the backup directory  
**When** the user runs `cap2obs --backup-dir /data/backups --obsidian-vault /vault --file "Capacities (2026-01-30 12-29-03).zip"`  
**Then** the tool SHALL use that specific file  
**And** SHALL NOT search for other files

---

#### Scenario: User specifies date-based selection

**Given** multiple backups from the same date exist  
**When** the user runs `cap2obs --backup-dir /data/backups --obsidian-vault /vault --date 2026-01-30`  
**Then** the tool SHALL filter files matching `Capacities (2026-01-30 *.zip)` pattern  
**And** SHALL select the file with the latest timestamp

---

#### Scenario: Automatic backup selection

**Given** no `--file` or `--date` argument is provided  
**When** the user runs `cap2obs --backup-dir /data/backups --obsidian-vault /vault`  
**Then** the tool SHALL scan all files matching `Capacities (YYYY-MM-DD HH-mm-ss).zip`  
**And** SHALL select the file with the most recent date and time

---

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

#### Scenario: Successful sync

**Given** sync completes without errors  
**When** the process exits  
**Then** it SHALL return exit code `0`

---

#### Scenario: Backup directory not found

**Given** the `--backup-dir` path does not exist  
**When** the tool validates arguments  
**Then** it SHALL log an error message  
**And** SHALL exit with code `1`

---

#### Scenario: No matching backup file

**Given** no files match the selection criteria  
**When** the tool searches for backups  
**Then** it SHALL log "No backup file found"  
**And** SHALL exit with code `2`

---

#### Scenario: Target vault path invalid

**Given** the `--obsidian-vault` path does not exist  
**When** the tool validates arguments  
**Then** it SHALL exit with code `3`

---

#### Scenario: ZIP extraction failure

**Given** the backup file is corrupted  
**When** the tool attempts extraction  
**Then** it SHALL log the error  
**And** SHALL exit with code `4`

---

#### Scenario: Permission denied

**Given** the user lacks read/write permissions  
**When** any file operation fails due to permissions  
**Then** it SHALL exit with code `5`

---

#### Scenario: Unexpected sync error

**Given** an unhandled exception occurs during sync  
**When** the error is caught  
**Then** it SHALL log the error details  
**And** SHALL exit with code `6`

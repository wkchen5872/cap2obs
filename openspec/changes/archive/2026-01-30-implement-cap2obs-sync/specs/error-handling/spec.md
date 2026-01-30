# Spec: Error Handling & Logging

## ADDED Requirements

### Requirement: Structured log format

The tool SHALL output logs in a consistent, parseable format.

#### Scenario: Standard log entry

**Given** any operation is performed  
**When** a log entry is created  
**Then** it SHALL follow format `[YYYY-MM-DD HH:MM:SS] [LEVEL] Message`  
**Where** LEVEL is one of: `INFO`, `ADD`, `MOD`, `SKIP`, `DEL`, `WARN`, `ERROR`

---

### Requirement: Console output

The tool SHALL display real-time progress to stdout.

#### Scenario: Sync progress display

**Given** sync is in progress  
**When** files are processed  
**Then** the tool SHALL output each operation to console  
**And** SHALL display a summary at completion with counts

---

### Requirement: File logging

The tool SHALL write detailed logs when `--log-file` is specified.

#### Scenario: Detailed file logging

**Given** the user specified `--log-file /var/log/cap2obs.log`  
**When** sync executes  
**Then** the tool SHALL write all log entries to the file  
**And** SHALL include additional details like hash values and file sizes  
**And** SHALL append to existing log file if present

---

### Requirement: Dry-run log annotation

The tool SHALL clearly mark dry-run operations in logs.

#### Scenario: Dry-run log prefix

**Given** the user runs with `--dry-run`  
**When** operations are logged  
**Then** each action log SHALL be prefixed with `[DRY-RUN]`  
**And** SHALL use format `[DRY-RUN] [ADD] Would add: notes/file.md`

---

### Requirement: Fail-fast error handling

The tool SHALL immediately terminate on critical errors.

#### Scenario: I/O error during sync

**Given** a file copy operation fails due to disk full  
**When** the error is caught  
**Then** the tool SHALL log error details  
**And** SHALL cleanup temporary files  
**And** SHALL exit with appropriate error code

---

### Requirement: Path validation

The tool SHALL validate all paths before operations.

#### Scenario: Backup directory validation

**Given** the user specifies `--backup-dir /invalid/path`  
**When** the tool initializes  
**Then** it SHALL check if the directory exists  
**And** SHALL log `[ERROR] Backup directory not found: /invalid/path`  
**And** SHALL exit with code `1`

---

#### Scenario: Vault directory validation

**Given** the user specifies `--obsidian-vault /invalid/vault`  
**When** the tool initializes  
**Then** it SHALL check if the directory exists  
**And** SHALL log `[ERROR] Obsidian vault not found: /invalid/vault`  
**And** SHALL exit with code `3`

---

### Requirement: Permission verification

The tool SHALL verify file system permissions before operations.

#### Scenario: Read permission check

**Given** the backup file lacks read permissions  
**When** extraction is attempted  
**Then** the tool SHALL log `[ERROR] Permission denied: <filename>`  
**And** SHALL exit with code `5`

---

#### Scenario: Write permission check

**Given** the vault directory is read-only  
**When** the tool attempts to write  
**Then** it SHALL log `[ERROR] Cannot write to vault: Permission denied`  
**And** SHALL exit with code `5`

---

### Requirement: Execution summary

The tool SHALL output a summary of operations performed.

#### Scenario: Sync completion summary

**Given** sync completes successfully  
**When** the tool exits  
**Then** it SHALL log `[INFO] SUCCESS: X added, Y modified, Z deleted`  
**And** SHALL include total file count processed

---

#### Scenario: No changes detected

**Given** all files match (hash identical)  
**When** sync completes  
**Then** it SHALL log `[INFO] SUCCESS: No changes detected`  
**And** SHALL exit with code `0`


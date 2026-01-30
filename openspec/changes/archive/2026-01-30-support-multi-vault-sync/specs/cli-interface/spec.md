# Spec: CLI Interface (Multi-Vault Update)

## MODIFIED Requirements

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

### Requirement: Exit code specification

The tool SHALL exit with standardized status codes for automation integration.

#### Scenario: Target root path invalid

**Given** the `--obsidian-root` (or `--obsidian-vault`) path does not exist  
**When** the tool validates arguments  
**Then** it SHALL exit with code `3`

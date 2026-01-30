# vault-detection Specification

## Purpose
TBD - created by archiving change support-multi-vault-sync. Update Purpose after archive.
## Requirements
### Requirement: Backup structure detection

The tool SHALL automatically detect whether the extracted backup contains a nested or flat structure.

#### Scenario: Nested structure with timestamp wrapper

**Given** a backup `Capacities (2026-01-30 12-29-03).zip` is extracted  
**And** the extracted content has structure `/temp/Capacities (2026-01-30 12-29-03)/Work/`  
**When** structure detection runs  
**Then** the tool SHALL identify this as a **nested** structure  
**And** SHALL enter the `Capacities (...)` folder  
**And** SHALL treat `Work` as a vault to sync

---

#### Scenario: Flat structure without wrapper

**Given** a backup is extracted  
**And** the extracted content has structure `/temp/Work/notes/...`  
**Where** `Work` does not match the timestamp pattern  
**When** structure detection runs  
**Then** the tool SHALL identify this as a **flat** structure  
**And** SHALL treat `Work` as a vault to sync directly

---

#### Scenario: Multiple vaults in nested structure

**Given** extracted content has structure:
```
/temp/Capacities (2026-01-30)/
├── Work/
├── Personal/
└── Projects/
```
**When** structure detection runs  
**Then** the tool SHALL return a list of three vaults: `Work`, `Personal`, `Projects`

---

#### Scenario: Single vault detection

**Given** extracted content has only one subdirectory `Work`  
**When** structure detection runs  
**Then** the tool SHALL return a list containing only `Work`

---

### Requirement: Vault folder identification

The tool SHALL correctly identify vault folders and exclude non-vault items.

#### Scenario: Files at root level are ignored

**Given** extracted content contains both folders and files at root level:
```
/temp/Capacities (2026-01-30)/
├── Work/        (directory)
├── README.txt   (file)
└── .DS_Store    (file)
```
**When** vault detection runs  
**Then** the tool SHALL only return `Work` as a vault  
**And** SHALL ignore files like `README.txt` and `.DS_Store`

---

#### Scenario: Hidden folders are excluded

**Given** extracted content contains:
```
/temp/Capacities (2026-01-30)/
├── Work/
├── .hidden_folder/
└── __MACOSX/
```
**When** vault detection runs  
**Then** the tool SHALL return only `Work`  
**And** SHALL exclude folders starting with `.` or `__`

---

### Requirement: Empty vault handling

The tool SHALL handle empty vault folders gracefully.

#### Scenario: Empty vault folder detected

**Given** a vault folder `Work` exists but is empty  
**When** vault detection runs  
**Then** the tool SHALL log `[WARN] Empty vault detected: Work`  
**And** SHALL exclude it from the sync list


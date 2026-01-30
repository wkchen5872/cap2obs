# scoped-sync Specification

## Purpose
TBD - created by archiving change support-multi-vault-sync. Update Purpose after archive.
## Requirements
### Requirement: Per-vault iterative sync

The tool SHALL synchronize each detected vault independently.

#### Scenario: Multiple vaults synced sequentially

**Given** detected vaults are `Work` and `Personal`  
**And** obsidian root is `/obsidian`  
**When** sync executes  
**Then** the tool SHALL sync `Temp/.../Work/` to `/obsidian/Work/`  
**And** SHALL sync `Temp/.../Personal/` to `/obsidian/Personal/`  
**And** SHALL log progress for each vault separately

---

#### Scenario: Vault sync creates missing target folder

**Given** backup contains vault `NewProject`  
**And** `/obsidian/NewProject/` does not exist  
**When** sync executes for `NewProject`  
**Then** the tool SHALL create `/obsidian/NewProject/`  
**And** SHALL log `[INFO] Creating new vault folder: NewProject`  
**And** SHALL proceed to sync content

---

### Requirement: Delete scope isolation

The tool SHALL strictly limit delete operations to the current vault scope.

#### Scenario: Files outside current vault are protected

**Given** backup contains only `Work`  
**And** obsidian root contains `Work` and `Family`  
**When** sync executes  
**Then** delete operations SHALL only occur within `/obsidian/Work/`  
**And** `/obsidian/Family/` SHALL remain completely untouched  
**And** no files in `Family` SHALL be deleted

---

#### Scenario: Root-level protection

**Given** obsidian root is `/obsidian`  
**And** backup vault `Work` has a file `notes/meeting.md`  
**When** sync deletes a removed file  
**Then** the tool SHALL NEVER delete `/obsidian/Work/` itself  
**And** SHALL NEVER delete any sibling folders of `Work`

---

#### Scenario: Delete within vault scope

**Given** backup vault `Work` does not contain `old-note.md`  
**And** `/obsidian/Work/old-note.md` exists  
**When** sync executes for `Work` vault  
**Then** the tool SHALL delete `/obsidian/Work/old-note.md`  
**And** SHALL log `[DEL] Work/old-note.md`

---

### Requirement: Per-vault statistics

The tool SHALL track and report sync statistics per vault.

#### Scenario: Per-vault progress logging

**Given** multiple vaults are being synced  
**When** each vault completes  
**Then** the tool SHALL log per-vault summary:
```
[INFO] Vault 'Work': 5 added, 2 modified, 1 deleted
[INFO] Vault 'Personal': 3 added, 0 modified, 0 deleted
```

---

#### Scenario: Aggregate summary at completion

**Given** sync completes for all vaults  
**When** the final summary is logged  
**Then** the tool SHALL show totals:
```
[INFO] SUCCESS: 2 vaults synced (8 added, 2 modified, 1 deleted)
```

---

### Requirement: Partial failure handling

The tool SHALL continue syncing remaining vaults if one fails.

#### Scenario: Permission error on one vault

**Given** vaults are `Work` and `Personal`  
**And** `/obsidian/Work/` has permission denied  
**When** sync executes  
**Then** the tool SHALL log `[ERROR] Failed to sync vault 'Work': Permission denied`  
**And** SHALL continue syncing `Personal`  
**And** SHALL exit with code 6 (partial failure)


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


---

### Requirement: Protected Files Exclusion

The tool SHALL NOT delete specific files or directories in the destination vault during synchronization, even if they are missing from the source backup (Capacities export). This ensures that Obsidian-specific configuration, plugins, and third-party tool metadata are preserved.

#### Scenario: Protected directories are preserved

**Given** destination vault contains `.obsidian/config` and `.git/config`  
**And** source backup does not contain these files  
**When** sync executes  
**Then** `.obsidian/config` SHALL NOT be deleted  
**And** `.git/config` SHALL NOT be deleted  
**And** the tool SHALL NOT log a deletion for these files

---

#### Scenario: Protected files are preserved

**Given** destination vault contains `.DS_Store`  
**And** source backup does not contain `.DS_Store`  
**When** sync executes  
**Then** `.DS_Store` SHALL NOT be deleted

---

#### Scenario: Prefix matching for protected paths

**Given** destination vault contains `.obsidian.mobile/` directory  
**And** source backup does not contain `.obsidian.mobile/`  
**When** sync executes  
**Then** `.obsidian.mobile/` and its contents SHALL NOT be deleted

---

#### Scenario: Non-protected files are deleted

**Given** destination vault contains `old_note.md`  
**And** `old_note.md` is not in the protected list  
**And** source backup does not contain `old_note.md`  
**When** sync executes  
**Then** `old_note.md` SHALL be deleted  
**And** the tool SHALL log `[DEL] old_note.md`

---

#### Scenario: Default protected list

**Given** no custom configuration is provided  
**When** sync executes  
**Then** the protected list SHALL include at least:
*   `.obsidian` (and any folder starting with `.obsidian`)
*   `.smart-env`
*   `.agents`
*   `.git`
*   `.claude`
*   `.gemini`
*   `.trash`
*   `.DS_Store`

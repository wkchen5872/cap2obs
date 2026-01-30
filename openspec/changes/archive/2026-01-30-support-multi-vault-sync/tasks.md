# Tasks: Support Multi-Vault Synchronization

This document outlines implementation steps for extending Cap2Obs to support multiple Obsidian vaults.

## Prerequisites

- `implement-cap2obs-sync` must be completed

---

## Implementation Tasks (Ordered)

### 1. Update CLI Parameter

**Deliverable:** `--obsidian-root` parameter with backwards compatibility

**Steps:**
- Rename `--obsidian-vault` to `--obsidian-root` in argument parser
- Add `--obsidian-vault` as hidden alias with deprecation warning
- Update help text and examples
- Update error messages to reference "obsidian root"

**Validation:**
- `cap2obs --help` shows `--obsidian-root`
- `cap2obs --obsidian-vault ...` works with deprecation warning
- README examples updated

**Related Specs:** `cli-interface`

---

### 2. Implement Vault Detection Module

**Deliverable:** `VaultDetector` class in `vault_detector.py`

**Steps:**
- Create `VaultDetector` class
- Implement `detect_structure()` method:
  - Check if single top-level folder matches `Capacities (...)` pattern
  - Return "nested" or "flat" structure type
- Implement `find_vaults()` method:
  - List subdirectories based on structure type
  - Filter out hidden folders (`.`, `__`)
  - Filter out empty folders with warning
  - Return list of vault paths

**Validation:**
- Unit test: nested structure detection
- Unit test: flat structure detection
- Unit test: hidden folder exclusion
- Unit test: empty vault warning

**Related Specs:** `vault-detection`

---

### 3. Refactor BackupProcessor

**Deliverable:** Updated extraction to return raw temp path

**Steps:**
- Modify `extract_backup()` to return temp directory root
- Remove `_find_content_root()` logic (moved to VaultDetector)
- Add method `get_extraction_root()` for vault detection

**Validation:**
- Extraction returns raw temp path
- Old tests still pass

**Related Specs:** `vault-detection`

---

### 4. Implement Scoped Sync Loop

**Deliverable:** Per-vault sync orchestration in CLI

**Steps:**
- After extraction, call `VaultDetector.find_vaults()`
- For each vault:
  - Determine target path: `obsidian_root / vault_name`
  - Create target folder if missing
  - Call `SyncEngine.sync(source_vault, target_vault)`
  - Collect stats per vault
- Aggregate final statistics
- Log per-vault and total summaries

**Validation:**
- Multi-vault backup syncs each vault
- Single-vault backup works as before
- Missing target folders are created

**Related Specs:** `scoped-sync`

---

### 5. Enforce Delete Scope Isolation

**Deliverable:** Verified delete protection

**Steps:**
- Review `SyncEngine._delete_file()` to ensure scope
- Add assertion: delete path must be within target vault
- Add tests for scope violation protection
- Log vault name prefix in delete operations

**Validation:**
- Delete operations only within current vault
- Files outside vault scope never deleted
- Test: vault A sync doesn't delete vault B files

**Related Specs:** `scoped-sync`

---

### 6. Enhance Logging for Multi-Vault

**Deliverable:** Per-vault progress indication

**Steps:**
- Add vault name to log messages during sync
- Format: `[INFO] [Work] Starting sync...`
- Add per-vault summary after each vault completes
- Add aggregate summary at end

**Validation:**
- Logs clearly indicate which vault is being synced
- Per-vault stats are reported correctly

**Related Specs:** `scoped-sync`

---

### 7. Handle Partial Failures

**Deliverable:** Graceful handling of per-vault errors

**Steps:**
- Wrap per-vault sync in try-except
- On error: log, mark vault as failed, continue
- Track success/failure count
- Exit code logic:
  - All succeed: 0
  - Some failed: 6 (partial failure)
  - All failed: 6

**Validation:**
- One vault permission error doesn't stop others
- Final summary shows partial failure

**Related Specs:** `scoped-sync`

---

### 8. Update Tests

**Deliverable:** Comprehensive test coverage for multi-vault

**Steps:**
- Add unit tests for `VaultDetector`
- Add integration test: multi-vault sync
- Add integration test: single-vault backwards compatibility
- Add test: delete scope isolation

**Validation:**
- All new tests pass
- Existing tests still pass
- Coverage maintained >80%

**Related Specs:** All specs

---

### 9. Update Documentation

**Deliverable:** Updated README and examples

**Steps:**
- Update README with `--obsidian-root` usage
- Add multi-vault sync explanation
- Update automation examples
- Add migration note for `--obsidian-vault` users

**Validation:**
- README reflects new behavior
- Examples work correctly

**Related Specs:** `cli-interface`

---

## Dependencies & Parallelization

- **Sequential:** Tasks 1-4 must be in order
- **Parallel:** Task 6-7 can run parallel after Task 4
- **Critical Path:** 1 → 2 → 3 → 4 → 5 → 8

---

## Verification Strategy

### Automated Tests
- Unit tests for vault detection logic
- Integration tests for multi-vault sync
- Scope isolation verification

### Manual Verification
1. Create test backup with multiple vaults
2. Sync to obsidian root with existing + new vaults
3. Verify: new vault created, existing synced, unrelated untouched
4. Test delete protection with vault-only in target

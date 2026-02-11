## Context

The current `SyncEngine` deletes any file in the target directory that is not present in the source backup. This default behavior is destructive for Obsidian vaults, which contain local configuration files (like `.obsidian`, `.git`, `.trash`) that are never part of the Capacities backup.

We need to make the deletion logic "aware" of these protected paths to prevent data loss.

## Goals / Non-Goals

**Goals:**
*   Prevent deletion of standard Obsidian configuration directories.
*   Prevent deletion of version control directories.
*   Prevent deletion of AI tool configurations.
*   Allow users to sync without losing their vault settings.

**Non-Goals:**
*   User-configurable ignore patterns (v1 is hardcoded for safety/simplicity).
*   Complex glob pattern matching (simple prefix/exact match is sufficient for v1).

## Decisions

### 1. Hardcoded Protected List vs Configurable
**Decision:** Use a hardcoded list of common protected paths for this iteration.
**Rationale:** The immediate need is to stop data loss for standard known paths. Adding a configuration system (`.cap2obsignore` or CLI args) adds complexity that can be addressed in a future "User Configuration" capability. The proposed list covers 99% of use cases.

### 2. Implementation in SyncEngine
**Decision:** Modify `SyncEngine._delete_file` caller loop in `sync()` method.
**Rationale:** The decision to delete is made in the diffing loop (lines 80-83 of `sync_engine.py`). Filtering there is most efficient and centralizes the logic.

### 3. Prefix Matching Logic
**Decision:** Use `str.startswith()` on relative path string representation.
**Rationale:** Simple and effective. Matches `.obsidian` and `.obsidian.mobile` automatically without complex path parsing.

## Implementation Details

### `SyncEngine` Class
- Add `_is_protected(self, rel_path: str) -> bool` helper method.
- Update `sync()` method to filter `files_to_delete` using `_is_protected`.

### `SyncEngine.sync` Loop Modification
```python
        # Process target-only files (DELETE)
        files_to_delete = target_relative - source_relative
        safe_to_delete = [
            f for f in files_to_delete 
            if not self._is_protected(str(f))
        ]
        
        for rel_path in sorted(safe_to_delete):
            target_file = target_root / rel_path
            self._delete_file(target_file, str(rel_path))
```

### Protected Paths Constant
```python
PROTECTED_PREFIXES = {
    ".obsidian", ".trash", ".git", ".smart-env", ".agents", 
    ".claude", ".gemini", ".DS_Store"
}
```

## Risks / Trade-offs

*   **Risk**: Hardcoded list might miss a user's custom folder.
    *   *Mitigation*: Document this limitation.
*   **Risk**: False positives (e.g., unintended matching).
    *   *Mitigation*: Include specific tests for corner cases.

## Verification Plan

### Automated Tests
Since no existing `test_sync_engine.py` exists, we will create it.

**New Test**: `tests/test_sync_engine.py` (using `pytest`)
- `test_sync_deletes_unprotected_files`: Verify `old.md` is deleted.
- `test_sync_preserves_protected_files`: Verify `.obsidian/config` is kept.
- `test_sync_preserves_protected_dirs`: Verify `.git/` tree is kept.
- `test_sync_preserves_prefix_matches`: Verify `.obsidian.mobile` is kept.

**Command**: `pytest tests/test_sync_engine.py`

### Manual Verification
1. Create a dummy "Target" vault with `.obsidian/config` and `note.md`.
2. Create a "Source" folder with only `note.md`.
3. Run sync.
4. Verify `.obsidian/config` exists.
5. Create "Source" folder without `note.md`.
6. Run sync.
7. Verify `note.md` is deleted but `.obsidian/config` remains.

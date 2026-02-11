## 1. Safety Verification First

- [ ] 1.1 Create `tests/test_sync_engine.py` with test cases for protected file deletion logic.
- [ ] 1.2 Implement dummy `SyncEngine` fixture and mock file system for tests.
- [ ] 1.3 Verify tests fail (or pass partially) with current implementation to establish baseline.

## 2. Core Implementation

- [ ] 2.1 Add `PROTECTED_PREFIXES` constant to `cap2obs/sync_engine.py`.
- [ ] 2.2 Implement `_is_protected(self, rel_path: str) -> bool` method in `SyncEngine` class.
- [ ] 2.3 Modify `sync()` method to filter `files_to_delete` using `_is_protected`.

## 3. Verification

- [ ] 3.1 Run `tests/test_sync_engine.py` to confirm all tests pass.
- [ ] 3.2 Run existing tests to ensure no regression in other sync logic.
- [ ] 3.3 (Manual) Perform a dry-run sync against a dummy vault to visually confirm protected files are skipped.

## 1. Create `markdown_utils.py` Module

- [x] 1.1 Create `cap2obs/markdown_utils.py` with module docstring.
- [x] 1.2 Implement `parse_frontmatter(content: str) -> dict[str, str]` — extract `cap2obs_source`, `cap2obs_managed`, `cap2obs_managed_date` from YAML frontmatter.
- [x] 1.3 Implement `inject_properties(content: str, source_id: str, managed: bool = False, managed_date: str = "") -> str` — insert or update cap2obs properties in markdown content.
- [x] 1.4 Implement `scan_markdown_index(directory: Path) -> dict[str, dict]` — scan directory for `.md` files and build `{cap2obs_source: {path, managed}}` index.
- [x] 1.5 Create `tests/test_markdown_utils.py` with tests for all public functions.
- [x] 1.6 Run `pytest tests/test_markdown_utils.py` — all tests pass.

## 2. Extend `SyncEngine` — Hash Pool for Media

- [x] 2.1 Add `MEDIA_EXTENSIONS` constant and `retained_paths` field to `SyncEngine`.
- [x] 2.2 Implement `_build_target_hash_pool(target_root: Path) -> dict[str, list[Path]]`.
- [x] 2.3 Implement `_is_media_file(path: Path) -> bool`.
- [x] 2.4 Update `sync()` to call `_build_target_hash_pool` before processing source files.
- [x] 2.5 Update source file loop: for non-`.md` files, check hash pool first; if matched, consume entry, add to `retained_paths`, SKIP.
- [x] 2.6 Update deletion phase: exclude `retained_paths` from `files_to_delete`.

## 3. Extend `SyncEngine` — Frontmatter Tracking for Markdown

- [x] 3.1 Implement `_build_target_md_index(target_root: Path) -> dict[str, dict]` using `scan_markdown_index`.
- [x] 3.2 Update `sync()` to call `_build_target_md_index` before processing source files.
- [x] 3.3 Update source file loop: for `.md` files, use MD index for match → `managed: true` = SKIP, `managed: false` = UPDATE (with property injection), not found = ADD (with property injection).
- [x] 3.4 Update deletion phase: orphan `.md` with `managed: true` → PROTECT; `managed: false` → DELETE.

## 4. Tests and Verification

- [x] 4.1 Add sync engine tests: hash pool skip, hash pool add, duplicate media, frontmatter managed skip, unmanaged update, new file injection, orphan protection, orphan deletion, retained media protection.
- [x] 4.2 Run full test suite `pytest tests/` — all existing + new tests pass.
- [x] 4.3 Manual dry-run verification against a representative vault structure.

## 5. TDD & Subagent Review Framework (Mandatory Execution Checklist)

> [!IMPORTANT]
> The following tasks define the required workflow execution for the AI agent during the implement phase (as required by `config.yaml`):

- [x] 5.1 Execute TDD cycle for Media Hash Pool implementation (Write tests, implement minimum code, refactor)
- [x] 5.2 Execute TDD cycle for Markdown Frontmatter tool logic (Write tests, implement, refactor)
- [ ] 5.3 Request Subagent Code Review for all newly integrated logic in `SyncEngine`
- [x] 5.4 Execute the `everything-claude-code` verification loop and AgentShield security scan
- [x] 5.5 Validate minimum 80% coverage via `pytest --cov=cap2obs tests/` before marking change as complete

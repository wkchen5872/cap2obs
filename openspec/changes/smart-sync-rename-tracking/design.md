## Context

The `SyncEngine` currently performs path-based 4-way sync (ADD/UPDATE/SKIP/DELETE). Users who reorganise files in Obsidian (rename, move) lose their work on the next sync because path identity is the only matching criterion. We need content-based identity for media and metadata-based identity for markdown, without adding any external dependencies.

## Goals / Non-Goals

**Goals:**
*   Recognise renamed media files via content hash matching.
*   Recognise renamed/curated markdown notes via `cap2obs_source` YAML property.
*   Protect curated files (`managed: true`) from overwrite and deletion.
*   Automatically inject tracking properties into synced markdown files.
*   Maintain backward compatibility — vaults without properties behave as before.

**Non-Goals:**
*   Full YAML parser (we only need to read/write three specific keys).
*   Bi-directional sync (edits in Obsidian do NOT propagate back to Capacities).
*   User-configurable property key names (hardcoded for v1).
*   Tracking renames of markdown files by content hash (markdown content changes when user edits).

## Decisions

### 1. Hash Pool Data Structure
**Decision:** Use `dict[str, list[Path]]` mapping hash → list of target paths (FIFO consumption via `pop()`).
**Rationale:** Handles duplicate files (same content, different names) correctly. When a source file's hash matches, one target entry is consumed. If more source files share the hash than target entries, the extras are treated as normal ADD.

### 2. Media vs Markdown Discrimination
**Decision:** Determine file type by extension — `.md` files use frontmatter strategy, everything else uses hash pool.
**Rationale:** Simple, deterministic, aligns with Capacities export structure where markdown and media are clearly separated. No ambiguity about which strategy to apply.

### 3. Frontmatter Parser Scope
**Decision:** Build a minimal parser in `cap2obs/markdown_utils.py` that:
- Detects `---` delimited YAML blocks at file start.
- Extracts `cap2obs_source`, `cap2obs_managed`, `cap2obs_managed_date` via regex line matching.
- Injects/updates these three keys without disturbing other YAML content.
**Rationale:** Avoids PyYAML dependency. The three keys are flat (no nesting), so regex is sufficient. Existing user properties (title, tags, etc.) are preserved.

### 4. Retained Paths Set
**Decision:** Maintain a `retained_paths: set[Path]` during sync. Populated during source dispatch phase. Queried during deletion phase.
**Rationale:** Clean separation of concerns. The source dispatch phase "claims" target files, and the deletion phase respects those claims. Works for both hash-matched media and frontmatter-matched markdown.

### 5. Property Injection Timing
**Decision:** Inject `cap2obs_source` during ADD (new file) and UPDATE (overwrite unmanaged). Never modify a `managed: true` file.
**Rationale:** The source backup content is the canonical source for unmanaged files. Once a user sets `managed: true`, the file is fully under their control — we never touch it again.

## Implementation Details

### New Module: `cap2obs/markdown_utils.py`

Leaf module, no imports from other `cap2obs` modules.

```python
# Public API:
def parse_frontmatter(content: str) -> dict[str, str]:
    """Extract cap2obs properties from YAML frontmatter."""

def inject_properties(content: str, source_id: str, managed: bool = False,
                      managed_date: str = "") -> str:
    """Inject or update cap2obs properties in markdown content."""

def scan_markdown_index(directory: Path) -> dict[str, dict]:
    """Scan directory for .md files, return {cap2obs_source: {path, managed}} index."""
```

### Modified: `cap2obs/sync_engine.py`

#### New Constants
```python
MEDIA_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp",
                    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
                    ".zip", ".rar", ".7z", ".tar", ".gz",
                    ".mp3", ".mp4", ".wav", ".mov", ".avi"}
```

#### New Fields in `SyncEngine.__init__`
```python
self.retained_paths: set[Path] = set()
```

#### New Methods
```python
def _build_target_hash_pool(self, target_root: Path) -> dict[str, list[Path]]:
    """Hash all non-.md files in target, returning {hash: [paths]}."""

def _build_target_md_index(self, target_root: Path) -> dict[str, dict]:
    """Scan target .md files for cap2obs_source property, returning index."""

def _is_media_file(self, path: Path) -> bool:
    """Check if file is a media/attachment (non-.md)."""
```

#### Modified `sync()` Flow
```
1. _build_target_hash_pool(target_root)    # Pre-scan media
2. _build_target_md_index(target_root)     # Pre-scan markdown
3. For each source file:
   a. If .md → use MD index strategy
   b. Else → use hash pool strategy
4. Deletion phase: filter out retained_paths + protected prefixes
```

### Modified: `cap2obs/cli.py`

No structural changes needed. `SyncEngine` API (`sync(source, target) -> SyncStats`) remains identical.

## Risks / Trade-offs

*   **Risk**: Media file whose content is edited AND renamed will not match hash → re-added with original name, and renamed version deleted (if not in protected dir).
    *   *Mitigation*: Document this edge case. Users can add custom directories to `PROTECTED_PREFIXES`.
*   **Risk**: First sync on existing vault with many media files will be slower due to full hash scan.
    *   *Mitigation*: Hash computation is fast (MD5) and amortised. Subsequent syncs benefit from SKIP optimisation.
*   **Risk**: Frontmatter injection modifies file content, changing its hash.
    *   *Mitigation*: This is expected. After injection, the file's hash in target will differ from source. Next sync will see `cap2obs_source` match and use managed/unmanaged logic instead of hash comparison.

## Engineering Disciplines

This implementation strictly follows the global engineering disciplines:
1. **Test-Driven Development (TDD)**: Test cases must be written before implementation (RED → GREEN → REFACTOR).
2. **Subagent-Driven Development**: All implementation tasks must undergo a subagent code review phase.
3. **Everything-Claude-Code Guidelines**: We align with `tdd-workflow`, `tdd-guide`, and `AgentShield security` principles.
4. **Coverage Requirement**: A minimum of **80% code coverage** is strictly required for the module to pass verification.
5. **Security Scan**: The final pipeline must include security scanning and a verification loop.

## Verification Plan

### Automated Tests
To meet the TDD and 80% coverage requirements, tests will be constructed *before* actual implementation:

**New**: `tests/test_markdown_utils.py`
- `test_parse_frontmatter_with_cap2obs_keys`: Parse existing properties.
- `test_parse_frontmatter_without_yaml`: Returns empty dict for files without frontmatter.
- `test_inject_properties_no_existing_yaml`: Creates `---` block with three keys.
- `test_inject_properties_with_existing_yaml`: Appends to existing block without disturbing other keys.
- `test_inject_properties_update_existing`: Overwrites existing `cap2obs_*` keys.
- `test_scan_markdown_index`: Builds correct index from directory of `.md` files.

**Updated**: `tests/test_sync_engine.py`
- `test_hash_pool_skip_renamed_media`: Renamed media with same hash is SKIP + retained.
- `test_hash_pool_add_when_no_match`: New media with no hash match is ADD.
- `test_hash_pool_duplicate_media`: Two source files with same hash, only one target file → one SKIP, one ADD.
- `test_md_frontmatter_managed_skip`: `managed: true` markdown is SKIP.
- `test_md_frontmatter_unmanaged_update`: `managed: false` markdown is UPDATE.
- `test_md_new_file_injects_properties`: New markdown file gets `cap2obs_source` injected.
- `test_orphan_managed_md_protected`: Orphan `managed: true` file is not deleted.
- `test_orphan_unmanaged_md_deleted`: Orphan `managed: false` file is deleted.
- `test_retained_media_not_deleted`: Retained (hash-matched) media is not deleted.

**Command**: `pytest tests/`

### Manual Verification
1. Set up a dummy vault with renamed images and curated markdown (with and without `cap2obs_managed: true`).
2. Run `cap2obs --dry-run` and verify log output matches expected SKIP / ADD / DELETE decisions.
3. Run without dry-run and confirm files on disk match expectations.

## Why

The current `SyncEngine` identifies files by **path only**. When a user renames or reorganises a file in the Obsidian vault (e.g. renaming `1BDD380D-87BA-495B-A6B8-627207020515.png` to `Snapshot_2023-01-15.png`), the next sync sees two mismatches:

1. The original path is missing in the target → **ADD** (re-creates the messy filename).
2. The renamed file is missing in the source → **DELETE** (destroys the user's curation work).

This defeats the purpose of managing notes locally in Obsidian while keeping Capacities as the upstream source of truth.

## What Changes

Introduce two complementary tracking strategies so that renamed/curated files are recognised and protected:

### Strategy 1 — Hash Pool for Media Files (Images, PDFs, binary attachments)

*   Before sync, build a `target_hashes: dict[str, list[Path]]` index by hashing every non-`.md` file in the target.
*   When processing each source media file, compute its hash. If a match is found in the pool, **consume** one entry from the pool, mark that target path as **retained**, and **SKIP** the source file.
*   The retained path is exempt from deletion even though the source lacks a file at that path.

### Strategy 2 — Frontmatter Properties for Markdown Notes

*   On first sync, inject three YAML properties into every `.md` file:
    ```yaml
    cap2obs_source: "<original stem>"
    cap2obs_managed: false
    cap2obs_managed_date:
    ```
*   Before sync, scan target `.md` files and build a `target_md_index: dict[str, dict]` keyed by `cap2obs_source`.
*   Matching logic per source `.md`:
    *   **Found + `managed: true`** → SKIP (user has curated this note).
    *   **Found + `managed: false`** → UPDATE (overwrite with latest backup content, re-inject properties).
    *   **Not found** → ADD (copy and inject properties).
*   Orphan logic:
    *   Target `.md` with `managed: false` and no matching source → DELETE.
    *   Target `.md` with `managed: true` and no matching source → PROTECT (keep).

## Capabilities

### Multi-Tool Compatibility
The planning and implementation of these capabilities are designed to be 100% compatible with:
- **Claude Code**: Primary tool for research and execution.
- **GitHub Copilot CLI**: Secondary interface for code generation.
- **Gemini CLI**: High-performance model integration.
- **Codex**: Legacy/Alternate execution engine.

All code and data structures generated can be seamlessly managed and extended by these tools.

### New Capabilities
- `markdown-frontmatter`: Lightweight YAML frontmatter parser and injector (pure stdlib, no external deps).

### Modified Capabilities
- `hash-sync`: Extended with hash-pool pre-scan and retained-path logic for media files.
- `scoped-sync`: Deletion phase now queries `retained_paths` before removing target-only files.

## Impact

*   **Sync Logic**: The core `SyncEngine.sync()` method gains two pre-processing phases (hash pool build + MD index build) and the deletion filter is augmented.
*   **New Module**: `cap2obs/markdown_utils.py` — leaf module (may be imported by `sync_engine`).
*   **Module Map Change**: `sync_engine` → `hasher` (existing) + `markdown_utils` (new).
*   **User Workflow**: Users set `cap2obs_managed: true` in Obsidian Properties UI after curating a note.
*   **No Breaking Changes**: Existing vaults without properties are treated as `managed: false` by default and behave the same as before.

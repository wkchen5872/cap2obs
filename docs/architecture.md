# 🏗️ Project Architecture Guide

*This file defines the structural integrity of the project. AI agents must respect these boundaries.*

## 1. Overview

Cap2Obs is a standalone Python CLI tool that synchronizes Capacities backup ZIP files to Obsidian vaults. It has **no external runtime dependencies** — only Python 3.10+ stdlib is required. It can be installed as a Python package or compiled into a self-contained binary via PyInstaller.

## 2. Directory Structure & Responsibilities

```
Cap2Obs/
├── cap2obs/                 # Main Python package
│   ├── __init__.py          # Package version declaration
│   ├── __main__.py          # Entry point: calls cli.main()
│   ├── cli.py               # Argument parsing, orchestration, ExitCode constants
│   ├── backup_processor.py  # ZIP file selection, filename parsing, extraction
│   ├── vault_detector.py    # Multi-vault structure detection (nested vs flat)
│   ├── sync_engine.py       # Hash-based 4-way sync logic (ADD/UPDATE/SKIP/DELETE)
│   ├── hasher.py            # MD5/SHA256 file content hashing
│   └── logger.py            # Structured logger (console + optional file output)
├── tests/                   # pytest test suite (mirrors cap2obs/ module names)
├── docs/                    # Project documentation
├── scripts/                 # build.sh (PyInstaller), other automation
├── openspec/                # OpenSpec change management artifacts
├── examples/                # Usage examples
├── setup.py                 # Package definition (pure stdlib, no install_requires)
└── Makefile                 # install / test / build / clean targets
```

## 3. Module Responsibilities & Call Graph

```
cli.py (orchestrator)
  └── backup_processor.py   → selects & extracts ZIP
  └── vault_detector.py     → finds vault folders in extracted content
  └── sync_engine.py        → performs 4-way file sync per vault
        └── hasher.py       → computes MD5 hash for file comparison
  └── logger.py             → structured log output (used by all modules)
```

**Dependency rules:**
- `cli.py` is the only orchestrator; it wires all modules together.
- `hasher.py` and `logger.py` are leaf modules — they must not import other `cap2obs` modules.
- All other modules depend only downward: `sync_engine` → `hasher`, never upward.

## 4. Technology Stack

| Layer | Choice |
|-------|--------|
| Language | Python 3.10+ |
| CLI parsing | `argparse` (stdlib) |
| File ops | `pathlib`, `shutil`, `zipfile` (stdlib) |
| Hashing | `hashlib` (stdlib) |
| Logging | Custom `Logger` class (stdout/stderr + optional file) |
| Testing | `pytest`, `pytest-cov` |
| Packaging | `setuptools`, `PyInstaller` (standalone binary) |
| No external runtime deps | ✅ Pure stdlib only |

## 5. Key Design Decisions

### 5.1 Four-Way Sync Logic (`sync_engine.py`)
Every file is evaluated against one of four outcomes:
- **ADD** — exists in source, missing in target → copy
- **UPDATE** — exists in both, hash differs → overwrite
- **SKIP** — exists in both, hash matches → no-op (preserves timestamp)
- **DELETE** — exists in target only, not protected → remove

### 5.2 Scope Protection
Delete operations are scoped to the vault being synced. Protected content is **never deleted or overwritten**:
- **Hidden files/folders:** `.obsidian`, `.trash`, `.git`, `.smart-env`, `.agents`, `.claude`, `.gemini`, `.github`, `.DS_Store`.
- **Important files:** `README.md`, `AGENTS.md`, `CLAUDE.md`.

### 5.3 Multi-Vault Detection (`vault_detector.py`)
Two backup structures are supported:
- **Nested:** `Capacities (YYYY-MM-DD HH-MM-SS)/VaultName/`
- **Flat:** `VaultName/` directly at the ZIP root

### 5.4 Temporary Workspace
Extraction uses `.temp_cap2obs/` adjacent to the backup directory. Cleanup is guaranteed via `atexit` + `SIGINT`/`SIGTERM` signal handlers registered in `BackupProcessor`.

### 5.5 Exit Codes (Automation-Friendly)

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Backup directory not found |
| 2 | No matching backup file found |
| 3 | Obsidian root path invalid |
| 4 | ZIP extraction failed |
| 5 | Permission denied |
| 6 | Unexpected sync error or partial failure |

### 5.6 Capacities to Obsidian Mapping
Cap2Obs handles the conversion from Capacities' space/object hierarchy to Obsidian's file/folder structure:
- **Space → Vault:** Each Capacities Space corresponds to one Obsidian Vault.
- **Object → Subfolder:** Capacities Objects become subfolders within the vault (e.g., Space `test` with Object `Project` → `test/Project/`).

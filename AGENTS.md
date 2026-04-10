# AGENTS.md — Cap2Obs Agent Guide

> AI agents working on this project must read this file before making any changes.
> See `docs/architecture.md` for module structure and `docs/conventions.md` for coding standards.

---

## Project Summary

**Cap2Obs** is a Python 3.10+ CLI tool that synchronizes Capacities backup ZIP files to Obsidian vaults. It has **zero external runtime dependencies** (pure stdlib). It can run as a pip package or as a standalone binary built with PyInstaller.

**Core workflow:** Select ZIP → Extract to `.temp_cap2obs/` → Detect vaults → Hash-based 4-way sync per vault (ADD/UPDATE/SKIP/DELETE) → Cleanup

---

## Key Commands

```bash
make install    # pip install -e .
make test       # pytest tests/
make build      # PyInstaller standalone binary → dist/cap2obs
make clean      # remove build artifacts
```

---

## Module Map

| File | Role |
|------|------|
| `cap2obs/cli.py` | Entry point, argument parsing, orchestration, `ExitCode` constants |
| `cap2obs/backup_processor.py` | ZIP file selection, filename parsing, extraction, temp dir lifecycle |
| `cap2obs/vault_detector.py` | Detects nested vs flat backup structure; lists vault folders |
| `cap2obs/sync_engine.py` | 4-way hash-based file sync; scope-protected deletions |
| `cap2obs/hasher.py` | MD5/SHA256 file hashing via `hashlib` |
| `cap2obs/logger.py` | Structured logger (stdout/stderr + optional file, dry-run aware) |

---

## Architecture Rules (from `docs/architecture.md`)

1. **`cli.py` is the sole orchestrator.** All other modules are called from there; they do not call each other except `sync_engine` → `hasher`.
2. **`hasher.py` and `logger.py` are leaf modules.** They must not import other `cap2obs` modules.
3. **No external runtime dependencies.** Keep everything in Python stdlib.
4. **Scope protection:** Delete operations never touch folders or files starting with `.obsidian`, `.trash`, `.git`, `.smart-env`, `.agents`, `.claude`, `.gemini`, `.github`, `.DS_Store`. Also protected are: `README.md`, `AGENTS.md`, `CLAUDE.md`.
5. **Temp dir cleanup** is guaranteed via `atexit` + signal handlers in `BackupProcessor`.

---

## Coding Rules (from `docs/conventions.md`)

- **Naming:** `snake_case` functions/vars, `PascalCase` classes, `UPPER_SNAKE_CASE` constants, `snake_case.py` files.
- **Type hints:** Always annotate all function signatures. Use `Optional[T]`, `List[T]`, `Path` from stdlib.
- **Docstrings:** Google-style on every public class and method. One-liner module docstring on every `.py` file.
- **Error handling:** Catch specific exceptions (`OSError`, `PermissionError`, etc.). Use `logger.error()` before returning failure. Use `ExitCode` constants in `cli.py`.
- **No `print()` in library code** — always use `self.logger.*` methods.
- **Logging methods:** `info`, `add`, `modify(path, reason)`, `skip`, `delete`, `warn`, `error`.
- **Class design:** `@dataclass` for data containers, `Enum` for bounded values, context manager protocol for resource-holding classes.
- **Tests:** In `tests/test_<module>.py`; use `tmp_path` fixture; one behaviour per test function.

---

## Adding a New Feature — Checklist

1. Identify which module owns the new behaviour (see Module Map above).
2. Keep `cli.py` as the only orchestrator — wire new module calls there.
3. Do not add external pip dependencies.
4. Add type hints and a Google-style docstring to every new function/method.
5. Add tests in `tests/test_<module>.py` using `tmp_path`.
6. Run `make test` before committing.

---

## Exit Codes (important for automation)

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Backup directory not found |
| 2 | No matching backup file found |
| 3 | Obsidian root path invalid |
| 4 | ZIP extraction failed |
| 5 | Permission denied |
| 6 | Unexpected sync error or partial failure |

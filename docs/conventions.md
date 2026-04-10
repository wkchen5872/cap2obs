# 📝 Coding Conventions & Styles

*This file defines the "Muscle Memory" for AI agents. Adhere to these styles strictly.*

## 1. Naming Conventions

| Kind | Convention | Example |
|------|-----------|---------|
| Variables & functions | `snake_case` | `find_vaults`, `backup_dir` |
| Classes | `PascalCase` | `BackupProcessor`, `SyncEngine` |
| Module files | `snake_case.py` | `sync_engine.py`, `vault_detector.py` |
| Constants (module-level) | `UPPER_SNAKE_CASE` | `PROTECTED_PREFIXES`, `TEMP_DIR_NAME` |
| Enums | `PascalCase` class, `UPPER_SNAKE_CASE` members | `LogLevel.ADD`, `StructureType.NESTED` |

## 2. Type Annotations

- **Always** annotate function signatures (parameters + return type).
- Use `Optional[T]` from `typing` for nullable values (Python 3.10 project).
- Use `List[T]`, `Set[T]`, `Tuple[T, ...]` from `typing` (not bare generics).
- Use `Path` from `pathlib` for all file system paths — never raw strings.

```python
# ✅ Correct
def find_vaults(self) -> List[Path]: ...

# ❌ Wrong
def find_vaults(self): ...
```

## 3. Docstrings

Use Google-style docstrings for all public classes and methods:

```python
def select_backup_file(
    self,
    explicit_file: Optional[str] = None,
    target_date: Optional[str] = None
) -> Optional[Path]:
    """
    Select backup file based on priority strategy.

    Args:
        explicit_file: Specific filename to use.
        target_date: Date string in YYYY-MM-DD format.

    Returns:
        Path to selected backup file or None if not found.
    """
```

- Module-level one-liner docstring required on every `.py` file.
- Keep comments meaningful — explain **why**, not what.

## 4. Error Handling

- Catch specific exceptions (`OSError`, `PermissionError`, `zipfile.BadZipFile`). Never use bare `except:`.
- Log errors via `logger.error()` before returning failure; do not `print()` in library code.
- Use the `ExitCode` constants in `cli.py` for all `sys.exit()` / `return` from `main()`.
- Operations that touch the filesystem must handle `OSError` and raise or return gracefully.

```python
# ✅ Correct
try:
    shutil.copy2(source, target)
except OSError as e:
    self.logger.error(f"Failed to add {rel_path}: {e}")
    raise
```

## 5. Prohibited Patterns

- ❌ No `print()` in library modules — use `self.logger` methods instead.
- ❌ No hardcoded paths or secrets.
- ❌ No external `pip` dependencies in production code — keep it pure stdlib.
- ❌ No logic-heavy `__init__` constructors; defer work to dedicated methods.
- ❌ Do not use `pathlib.Path` `.as_posix()` for OS comparisons — use `str(path)` or relative paths.

## 6. Logging

Use the `Logger` class methods consistently:

| Method | When to use |
|--------|------------|
| `logger.info(msg)` | General status messages |
| `logger.add(rel_path)` | File was added |
| `logger.modify(rel_path, reason)` | File was updated (always include reason) |
| `logger.skip(rel_path)` | File skipped (identical hash) |
| `logger.delete(rel_path)` | File deleted |
| `logger.warn(msg)` | Non-fatal issues (writes to stderr) |
| `logger.error(msg)` | Errors (writes to stderr) |

- Pass `Logger` instances down via constructor injection; never instantiate inside leaf modules.

## 7. Class Design

- Use `@dataclass` for plain data containers (e.g., `SyncStats`).
- Use `Enum` for bounded sets of values (e.g., `LogLevel`, `StructureType`).
- Implement context manager protocol (`__enter__`/`__exit__`) on classes that hold resources (e.g., `Logger`).
- Register cleanup handlers via `atexit` and signal handlers for classes managing temp state (e.g., `BackupProcessor`).

## 8. Testing

- Tests live in `tests/` with filenames mirroring the module: `test_sync_engine.py` → `sync_engine.py`.
- Use `tmp_path` pytest fixture for all temporary file operations.
- Write one test function per behaviour; name it `test_<scenario>_<expectation>`.
- Run tests: `pytest tests/` or `make test`.
- Run with coverage: `pytest --cov=cap2obs tests/`.

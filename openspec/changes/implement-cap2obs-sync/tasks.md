# Tasks: Implement Cap2Obs Smart Sync

This document outlines the ordered implementation steps for the Cap2Obs Smart Sync tool. Each task delivers user-visible progress and includes validation checkpoints.

## Prerequisites

1. **Choose implementation language**
   - Confirm with user: Python 3.10+ or Node.js 18 LTS+
   - Create project structure accordingly

---

## Core Implementation (Ordered)

### 1. Setup Project Foundation

**Deliverable:** Executable CLI entry point with version output

**Steps:**
- Create project repository structure
- Initialize package/module configuration (setup.py / package.json)
- Implement basic CLI parser with `--version` flag
- Add development dependencies (testing framework)

**Validation:**
- Run `cap2obs --version` → outputs version string
- Run `cap2obs --help` → displays usage information

**Related Specs:** `cli-interface`

---

### 2. Implement Argument Parsing & Validation

**Deliverable:** Full CLI argument handling with path validation

**Steps:**
- Implement required arguments: `--backup-dir`, `--obsidian-vault`
- Implement optional arguments: `--date`, `--file`, `--dry-run`, `--log-file`, `--keep-days`
- Add path existence validation for both required directories
- Add exit code mapping (codes 1, 3)

**Validation:**
- Run with missing required args → displays error and help text
- Run with non-existent paths → exits with appropriate error code
- Run with valid paths → passes validation

**Related Specs:** `cli-interface`, `error-handling`

---

### 3. Implement Logging System

**Deliverable:** Structured logging to console and optional file

**Steps:**
- Create logger module with timestamp formatting
- Implement log levels: INFO, ADD, MOD, SKIP, DEL, WARN, ERROR
- Add console output handler (stdout/stderr)
- Add optional file output handler based on `--log-file` argument
- Implement dry-run prefix logic

**Validation:**
- Log sample messages → verify format matches `[YYYY-MM-DD HH:MM:SS] [LEVEL] Message`
- Enable `--log-file` → verify file is created and written
- Enable `--dry-run` → verify `[DRY-RUN]` prefix appears

**Related Specs:** `error-handling`

---

### 4. Implement Backup File Selection

**Deliverable:** Auto-selection and date/file filtering logic

**Steps:**
- Implement filename pattern parser for `Capacities (YYYY-MM-DD HH-mm-ss).zip`
- Implement three-tier selection strategy:
  1. Explicit `--file` → use directly
  2. `--date` filter → select latest from matching files
  3. Auto-select → pick most recent overall
- Add error handling for "no file found" (exit code 2)

**Validation:**
- Create test directory with multiple dated backup files
- Run without args → selects newest file
- Run with `--date 2026-01-30` → selects correct file
- Run with `--file "specific.zip"` → uses that file
- Run with non-existent date → exits with code 2

**Related Specs:** `cli-interface`, `backup-processing`

---

### 5. Implement ZIP Extraction & Cleanup

**Deliverable:** Temporary workspace management

**Steps:**
- Create `.temp_cap2obs/` temporary directory
- Implement ZIP extraction using native library (zipfile / adm-zip)
- Implement content root detection (handle nested structures)
- Add cleanup logic with try-finally to ensure temp deletion
- Handle SIGINT/SIGTERM signals for graceful cleanup

**Validation:**
- Extract test ZIP → verify contents in `.temp_cap2obs/`
- Simulate error mid-extraction → verify cleanup still occurs
- Send SIGINT during extraction → verify cleanup happens

**Related Specs:** `backup-processing`, `error-handling`

---

### 6. Implement Content Hashing Module

**Deliverable:** File hash computation utility

**Steps:**
- Create hash function using MD5 or SHA256 (hashlib / crypto)
- Implement file content reading in chunks for memory efficiency
- Add hash computation for both text and binary files

**Validation:**
- Hash known test file → compare against expected hash
- Hash large file (>10MB) → verify no memory issues
- Hash binary image → verify correctness

**Related Specs:** `hash-sync`

---

### 7. Implement Sync Logic (Core Algorithm)

**Deliverable:** Four-way sync engine (Add/Update/Skip/Delete)

**Steps:**
- Implement recursive directory traversal for source
- For each source file:
  - Check if exists in target
  - Compute hashes if target exists
  - Determine action: ADD, UPDATE, SKIP
- Scan target for files not in source (DELETE candidates)
- Implement file copy/overwrite/delete operations
- Add directory creation for nested structures
- Respect `--dry-run` flag (skip actual operations)

**Validation:**
- Create test scenarios:
  - New file in source → verify ADD
  - Modified file (different hash) → verify UPDATE
  - Unchanged file (same hash) → verify SKIP, check timestamp preserved
  - Deleted file (only in target) → verify DELETE
- Run in `--dry-run` → verify no actual changes occur

**Related Specs:** `hash-sync`, `error-handling`

---

### 8. Implement Old Backup Cleanup (Optional Feature)

**Deliverable:** Automatic deletion of old backups based on `--keep-days`

**Steps:**
- Parse `--keep-days` argument
- After successful sync, scan backup directory
- Calculate file age from filename date
- Delete files older than threshold
- Log each deletion

**Validation:**
- Create backups with various dates (some >7 days old)
- Run with `--keep-days 7` → verify old files deleted
- Run without flag → verify no deletions

**Related Specs:** `cli-interface`

---

### 9. End-to-End Integration

**Deliverable:** Complete working tool with all features

**Steps:**
- Integrate all modules into main execution flow
- Add execution summary output
- Implement all exit codes (0-6)
- Handle all error paths with proper cleanup

**Validation:**
- Run full sync with real Capacities backup → Obsidian vault
- Verify Git diff shows only actual content changes (not timestamp changes)
- Test error scenarios:
  - Missing backup dir → exit 1
  - No files found → exit 2
  - Invalid vault → exit 3
  - Corrupted ZIP → exit 4
  - Permission denied → exit 5
- Verify log output format matches spec

**Related Specs:** All specs

---

### 10. Automated Testing Suite

**Deliverable:** Comprehensive test coverage

**Steps:**
- Create unit tests for:
  - Filename parsing
  - Hash computation
  - Sync decision logic
  - Path validation
- Create integration tests:
  - Full sync with mock data
  - Dry-run mode verification
  - Error handling paths
- Achieve >80% code coverage

**Validation:**
- Run test suite → all tests pass
- Generate coverage report → verify >80%

**Related Specs:** All specs

---

### 11. Documentation & Automation Setup

**Deliverable:** README and cron example

**Steps:**
- Create README.md with:
  - Installation instructions
  - Usage examples
  - All CLI arguments documented
  - Exit code reference table
- Add cron setup example
- Create example automation script

**Validation:**
- Follow README install steps on clean system → verify success
- Setup cron job using provided example → verify scheduled execution

**Related Specs:** `cli-interface`

---

## Dependencies & Parallelization

- **Sequential:** Tasks 1-5 must be completed in order
- **Parallel Opportunities:**
  - Task 6 (Hashing) can be developed alongside Tasks 3-5
  - Task 8 (Cleanup) can be developed after Task 4, in parallel with Tasks 5-7
- **Critical Path:** 1 → 2 → 3 → 4 → 5 → 7 → 9 → 10

---

## Verification Strategy

### Automated Tests
- Unit tests for all core functions (hashing, parsing, sync logic)
- Integration tests for full sync workflow
- Error path testing for all exit codes

### Manual Verification
1. **Real-world sync test:**
   - User provides actual Capacities backup
   - Sync to test Obsidian vault
   - Verify Git diff shows minimal changes (only content modifications)
   - Confirm cloud sync (iCloud/Git) shows clean history

2. **Cron automation test:**
   - Setup daily cron job
   - Monitor logs over 7 days
   - Verify reliability and performance

3. **Edge case validation:**
   - Test with large vaults (1000+ files)
   - Test with large binary assets (images >10MB)
   - Test interrupted syncs (SIGINT handling)

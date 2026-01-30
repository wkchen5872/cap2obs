# Proposal: Implement Cap2Obs Smart Sync

**Change ID:** `implement-cap2obs-sync`  
**Status:** Draft  
**Created:** 2026-01-30

## Executive Summary

This change introduces **Cap2Obs Smart Sync**, a command-line utility that automates the synchronization of Capacities daily backup exports to an Obsidian vault. The tool implements intelligent, hash-based content comparison to ensure minimal file modifications, preserving clean version histories for cloud sync services (iCloud, Obsidian Sync, Git).

## Problem Statement

Users who rely on both Capacities and Obsidian need a reliable way to:
1. Mirror Capacities backup data into their Obsidian vault
2. Avoid unnecessary file timestamp changes that pollute cloud sync histories
3. Handle incremental updates efficiently using content-based comparison
4. Automate the process for daily scheduled execution

## Proposed Solution

Implement a cross-platform (Linux, macOS) CLI tool with the following characteristics:

- **Content Hash Comparison**: Use MD5/SHA256 hashing to detect actual content changes, skipping files with identical content to preserve modification timestamps
- **Smart Sync Logic**: Add new files, update modified files, delete removed files, skip unchanged files
- **Flexible Input**: Support multiple ways to specify backup sources (auto-selection, date-based, explicit filename)
- **Safe Operations**: Dry-run mode, detailed logging, fail-fast error handling
- **Automation-Ready**: Designed for cron/scheduled execution with proper exit codes

## Scope

This change encompasses four core capabilities:

1. **CLI Interface** (`cli-interface`)
   - Argument parsing for backup directory, vault path, date/file selection
   - Dry-run and logging options
   - Exit code definitions for automation

2. **Backup Processing** (`backup-processing`)
   - ZIP file extraction to temporary workspace
   - Automatic source file selection based on date/filename patterns
   - Cleanup of temporary files

3. **Content Hash Sync** (`hash-sync`)
   - Recursive directory comparison using content hashing
   - Four-way sync logic (Add/Update/Skip/Delete)
   - Preservation of unchanged file timestamps

4. **Error Handling** (`error-handling`)
   - Comprehensive logging with structured format
   - Fail-fast rollback strategy
   - Standardized exit codes

## Technology Choice

The tool may be implemented in **either**:
- **Python 3.10+** (recommended): `pathlib`, `zipfile`, `hashlib`, `shutil`, `argparse`
- **Node.js 18 LTS+**: `fs/promises`, `crypto`, `adm-zip`/`yauzl`, `commander`/`yargs`

Both stacks provide native support for file operations and hashing without external system dependencies.

## User Review Required

> [!IMPORTANT]
> **Language Implementation Choice**
> 
> The specification supports both Python and Node.js implementations. Please confirm your preferred language stack before proceeding to implementation phase.

> [!WARNING]
> **Rollback Strategy**
> 
> This tool uses a **fail-fast** approach without local snapshots. Recovery relies on Obsidian's cloud sync version control (iCloud/Git). Users must ensure their vault is properly backed up by a cloud service before first use.

## Dependencies

- **System**: `unzip` utility (if not using native language libraries)
- **Runtime**: Python 3.10+ or Node.js 18 LTS+
- **External Services**: None

## Out of Scope

- Bidirectional synchronization (Obsidian → Capacities)
- Conflict resolution for simultaneous edits
- Graphical user interface
- Windows support (initially)

## Next Steps

1. Review and approve this proposal
2. Proceed with spec delta creation for each capability
3. Implement ordered task list
4. Validate with `openspec validate --strict`

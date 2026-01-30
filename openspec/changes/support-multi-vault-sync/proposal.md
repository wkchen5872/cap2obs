# Proposal: Support Multi-Vault Synchronization

**Change ID:** `support-multi-vault-sync`  
**Status:** Draft  
**Created:** 2026-01-30  
**Parent Change:** `implement-cap2obs-sync`

## Executive Summary

This change extends Cap2Obs to support **multiple Obsidian vaults** within a single backup. The key modifications include:
1. Renaming `--obsidian-vault` to `--obsidian-root` (root directory containing multiple vaults)
2. Automatic detection of backup structure (nested vs flat)
3. Iterative synchronization per vault
4. Scope-isolated delete protection

## Problem Statement

The current implementation assumes a 1:1 mapping between backup and vault. However, Capacities users often have multiple spaces (Work, Personal, etc.) that export as separate subdirectories within a single ZIP backup. The current tool cannot:
1. Detect whether a backup contains single or multiple vaults
2. Sync each vault to its corresponding target folder
3. Protect unrelated vaults from accidental deletion

## Proposed Solution

### 1. CLI Parameter Change

| Old Parameter | New Parameter | Description |
|---------------|---------------|-------------|
| `--obsidian-vault` | `--obsidian-root` | Root directory containing one or more vault folders |

### 2. Structure Detection

After ZIP extraction, detect the backup structure:

**Scenario A (Nested/Multi-Vault):**
```
Capacities (2026-01-30)/
├── Work/
│   └── notes/...
└── Personal/
    └── notes/...
```

**Scenario B (Single Vault):**
```
Work/
└── notes/...
```

### 3. Iterative Vault Sync

For each detected vault:
1. Map source: `Temp/.../[VaultName]/` → target: `--obsidian-root/[VaultName]/`
2. Create target vault folder if it doesn't exist
3. Execute hash-based sync within vault scope only

### 4. Delete Protection (Scope Isolation)

**Critical Safety Rule:** Delete operations are strictly limited to the current vault being synced. Other folders in `--obsidian-root` are never touched.

Example:
- Backup contains: `Work`, `Personal`
- Obsidian root contains: `Work`, `Personal`, `Family`
- Result: `Family` is untouched (not in backup, not deleted)

## Scope

This change modifies three capabilities:

1. **CLI Interface** (`cli-interface`)
   - Rename `--obsidian-vault` → `--obsidian-root`
   - Add backwards compatibility alias
   - Update help text and examples

2. **Vault Detection** (`vault-detection`)
   - Implement structure detection algorithm
   - Return list of vault paths to sync

3. **Scoped Sync** (`scoped-sync`)
   - Modify sync engine to iterate per vault
   - Enforce delete scope isolation

## User Review Required

> [!WARNING]
> **Breaking Change**
> 
> The `--obsidian-vault` parameter will be deprecated in favor of `--obsidian-root`. Existing scripts should be updated. A backwards-compatible alias will be provided for transition.

> [!IMPORTANT]
> **Behavior Change**
> 
> Vaults not present in the backup will NOT be deleted from `--obsidian-root`. This is the intended protection mechanism.

## Dependencies

- Builds on `implement-cap2obs-sync` (must be implemented first)
- No new external dependencies

## Out of Scope

- GUI for vault mapping configuration
- Selective vault filtering (sync only specific vaults)
- Cross-vault file deduplication

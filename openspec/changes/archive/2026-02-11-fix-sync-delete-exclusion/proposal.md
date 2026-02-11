## Why

The current synchronization logic is too aggressive when cleaning up "stale" files in the destination (Obsidian vault). Because Capacities backups do not contain Obsidian-specific configuration files (like `.obsidian`, `.git`, `.trash`), the tool incorrectly identifies them as deleted from the source and removes them from the destination.

This causes a critical issue where users lose their plugins, themes, and AI settings after every sync, forcing them to reconfigure their environment repeatedly.

## What Changes

To resolve this, we will introduce a **file protection mechanism** during the deletion phase of the synchronization process.

*   **Exclusion Filter**: Before deleting any file or directory in the destination, the tool will check if it matches a "protected list".
*   **Default Protected Paths**: The following paths will be protected by default and will **never** be deleted by the sync tool, even if they are missing from the source:
    *   `.obsidian` (and any folder starting with `.obsidian`, e.g., `.obsidian.mobile`)
    *   `.smart-env`
    *   `.agents`
    *   `.git`
    *   `.claude`
    *   `.gemini`
    *   `.trash`
    *   `.DS_Store`
*   **Prefix Matching**: The protection logic will support prefix matching to cover variations (like `.obsidian*`).
*   **Logic Update**:
    *   *Current*: `If (Target Has File) AND (Source Does Not Have File) -> DELETE`
    *   *New*: `If (Target Has File) AND (Source Does Not Have File) AND (NOT Protected) -> DELETE`

## Capabilities

### New Capabilities
<!-- No entirely new capabilities are being introduced that require separate specs. -->

### Modified Capabilities
- `scoped-sync`: The synchronization logic will be updated to include the exclusion filter in the deletion requirements.

## Impact

*   **Sync Logic**: The core sync loop (specifically the deletion handling) will be modified.
*   **User Config**: No new user configuration is required immediately, but the hardcoded list protects standard Obsidian and AI/Dev tool configurations.
*   **Safety**: Significantly reduces the risk of data loss for configuration files.

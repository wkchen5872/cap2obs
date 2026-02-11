## ADDED Requirements

### Requirement: Protected Files Exclusion

The tool SHALL NOT delete specific files or directories in the destination vault during synchronization, even if they are missing from the source backup (Capacities export). This ensures that Obsidian-specific configuration, plugins, and third-party tool metadata are preserved.

#### Scenario: Protected directories are preserved
- **Given** destination vault contains `.obsidian/config` and `.git/config`
- **And** source backup does not contain these files
- **When** sync executes
- **Then** `.obsidian/config` SHALL NOT be deleted
- **And** `.git/config` SHALL NOT be deleted
- **And** the tool SHALL NOT log a deletion for these files

#### Scenario: Protected files are preserved
- **Given** destination vault contains `.DS_Store`
- **And** source backup does not contain `.DS_Store`
- **When** sync executes
- **Then** `.DS_Store` SHALL NOT be deleted

#### Scenario: Prefix matching for protected paths
- **Given** destination vault contains `.obsidian.mobile/` directory
- **And** source backup does not contain `.obsidian.mobile/`
- **When** sync executes
- **Then** `.obsidian.mobile/` and its contents SHALL NOT be deleted

#### Scenario: Non-protected files are deleted
- **Given** destination vault contains `old_note.md`
- **And** `old_note.md` is not in the protected list
- **And** source backup does not contain `old_note.md`
- **When** sync executes
- **Then** `old_note.md` SHALL be deleted
- **And** the tool SHALL log `[DEL] old_note.md`

#### Scenario: Default protected list
- **Given** no custom configuration is provided
- **When** sync executes
- **Then** the protected list SHALL include at least:
  - `.obsidian` (and any folder starting with `.obsidian`)
  - `.smart-env`
  - `.agents`
  - `.git`
  - `.claude`
  - `.gemini`
  - `.trash`
  - `.DS_Store`

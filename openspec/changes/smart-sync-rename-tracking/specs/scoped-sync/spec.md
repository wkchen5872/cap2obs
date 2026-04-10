## ADDED Requirements

### Requirement: Frontmatter-based markdown tracking

The tool SHALL inject and track `cap2obs_source`, `cap2obs_managed`, and `cap2obs_managed_date` YAML properties in synced markdown files to enable rename-aware synchronization.

#### Scenario: New markdown receives tracking properties

- **Given** source contains `1BDD380D.md`
- **And** no markdown in target has `cap2obs_source: "1BDD380D"`
- **When** sync executes
- **Then** the file SHALL be copied to target (ADD)
- **And** the file SHALL contain YAML frontmatter with:
  ```yaml
  cap2obs_source: "1BDD380D"
  cap2obs_managed: false
  cap2obs_managed_date:
  ```

#### Scenario: Unmanaged markdown is overwritten on update

- **Given** source contains `note.md` (stem: `note`)
- **And** target contains `my_note.md` with `cap2obs_source: "note"` and `cap2obs_managed: false`
- **When** sync executes
- **Then** `my_note.md` SHALL be overwritten with source content (UPDATE)
- **And** the updated file SHALL retain `cap2obs_source: "note"` and `cap2obs_managed: false`

#### Scenario: Managed markdown is skipped

- **Given** source contains `note.md` (stem: `note`)
- **And** target contains `curated_note.md` with `cap2obs_source: "note"` and `cap2obs_managed: true`
- **When** sync executes
- **Then** `curated_note.md` SHALL NOT be modified (SKIP)
- **And** `note.md` SHALL NOT be added
- **And** the tool SHALL log `[SKIP] note.md`

#### Scenario: Orphan unmanaged markdown is deleted

- **Given** target contains `old_note.md` with `cap2obs_source: "old"` and `cap2obs_managed: false`
- **And** source does NOT contain `old.md`
- **When** sync executes
- **Then** `old_note.md` SHALL be deleted
- **And** the tool SHALL log `[DEL] old_note.md`

#### Scenario: Orphan managed markdown is protected

- **Given** target contains `curated_note.md` with `cap2obs_source: "removed"` and `cap2obs_managed: true`
- **And** source does NOT contain `removed.md`
- **When** sync executes
- **Then** `curated_note.md` SHALL NOT be deleted

### Requirement: Backward compatibility for untagged files

The tool SHALL treat markdown files without `cap2obs_source` property as path-based sync targets (existing behaviour).

#### Scenario: Legacy file without properties

- **Given** target contains `legacy.md` without any `cap2obs_*` properties
- **And** source contains `legacy.md`
- **When** sync executes
- **Then** the tool SHALL apply standard hash-based ADD/UPDATE/SKIP logic
- **And** SHALL inject `cap2obs_source: "legacy"` and `cap2obs_managed: false` into the target file

## ADDED Requirements

### Requirement: Hash-pool media rename tracking

The tool SHALL detect renamed media files by comparing content hashes rather than file paths, preventing duplicate additions and protecting curated files from deletion.

#### Scenario: Renamed media file is skipped

- **Given** source contains `1BDD380D.png` with hash H1
- **And** target contains `Snapshot_2023.png` with hash H1 (user renamed it)
- **When** sync executes
- **Then** `1BDD380D.png` SHALL NOT be copied to target (SKIP)
- **And** `Snapshot_2023.png` SHALL NOT be deleted
- **And** the tool SHALL log `[SKIP] 1BDD380D.png`

#### Scenario: Duplicate source files with one target match

- **Given** source contains `A.png` (hash H1) and `B.png` (hash H1)
- **And** target contains only `renamed.png` (hash H1)
- **When** sync executes
- **Then** one source file SHALL be SKIP (matched to `renamed.png`)
- **And** the other source file SHALL be ADD (no remaining pool entry)
- **And** `renamed.png` SHALL NOT be deleted

#### Scenario: Truly new media file is added normally

- **Given** source contains `new_diagram.png` with hash H2
- **And** no file in target has hash H2
- **When** sync executes
- **Then** `new_diagram.png` SHALL be copied to target (ADD)
- **And** the tool SHALL log `[ADD] new_diagram.png`

#### Scenario: Media file with same path but different hash is updated

- **Given** source contains `diagram.png` (hash H3)
- **And** target contains `diagram.png` (hash H4)
- **When** sync executes
- **Then** source SHALL overwrite target (UPDATE)
- **And** the tool SHALL log `[MOD] diagram.png (Hash mismatch)`

### Requirement: Retained path deletion protection

Target files matched via hash pool SHALL be exempt from deletion even when no source file shares their path.

#### Scenario: Hash-matched file not deleted

- **Given** target file `Images/curated/my_photo.jpg` was matched by hash pool
- **And** no source file exists at path `Images/curated/my_photo.jpg`
- **When** deletion phase executes
- **Then** `Images/curated/my_photo.jpg` SHALL NOT be deleted

### Requirement: Multi-Tool Environment Validation

All implementation scripts and checks SHALL be compatible across multiple AI IDEs, acknowledging distinct execution environments.

#### Scenario: Verify AI environment variables

- **Given** the sync script is executed by an AI agent
- **When** checking the environment context
- **Then** the script SHALL gracefully handle execution regardless of whether `CLAUDE_PROJECT_DIR`, `GEMINI_PROJECT_DIR`, or `GITHUB_COPILOT_WORKSPACE` are present
- **And** SHALL NOT fail if executed standalone without any of these tool-specific variables.

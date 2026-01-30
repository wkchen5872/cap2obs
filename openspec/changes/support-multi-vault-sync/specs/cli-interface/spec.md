# Spec: CLI Interface (Multi-Vault Update)

## MODIFIED Requirements

### Requirement: Command-line argument for target directory

The tool SHALL accept `--obsidian-root` as the target directory parameter.

#### Scenario: User specifies obsidian root directory

**Given** the user has an Obsidian root containing multiple vaults at `/obsidian`  
**And** the vaults include `Work`, `Personal`, and `Family`  
**When** they run `cap2obs --backup-dir /backups --obsidian-root /obsidian`  
**Then** the tool SHALL validate the root path exists  
**And** SHALL proceed to detect and sync vaults within this root

---

#### Scenario: Backwards compatibility with deprecated parameter

**Given** the user has an existing script using `--obsidian-vault`  
**When** they run `cap2obs --backup-dir /backups --obsidian-vault /obsidian`  
**Then** the tool SHALL accept the parameter as an alias for `--obsidian-root`  
**And** SHALL log a deprecation warning: `[WARN] --obsidian-vault is deprecated, use --obsidian-root instead`  
**And** SHALL proceed with synchronization normally

---

#### Scenario: Help text reflects new parameter name

**Given** the user runs `cap2obs --help`  
**When** the help text is displayed  
**Then** it SHALL show `--obsidian-root PATH` as the required parameter  
**And** SHALL describe it as "Root directory containing Obsidian vault folders"  
**And** SHALL NOT show the deprecated `--obsidian-vault` parameter

---

### Requirement: Updated usage examples

The tool help text SHALL include updated examples reflecting multi-vault usage.

#### Scenario: Example shows root directory usage

**Given** the user runs `cap2obs --help`  
**When** viewing the examples section  
**Then** examples SHALL use `--obsidian-root` instead of `--obsidian-vault`  
**And** SHALL show: `cap2obs --backup-dir /backups --obsidian-root /home/user/obsidian`

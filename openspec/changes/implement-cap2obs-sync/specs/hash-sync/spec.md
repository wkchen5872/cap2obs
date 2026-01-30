# Spec: Content Hash Synchronization

## ADDED Requirements

### Requirement: File content hashing

The tool SHALL compute cryptographic hashes to detect content changes.

#### Scenario: Hash computation for comparison

**Given** a file exists in both source and target  
**When** the sync engine compares them  
**Then** it SHALL compute MD5 or SHA256 hash of source file content  
**And** SHALL compute the same hash for target file content  
**And** SHALL compare the hash values

---

### Requirement: Add operation

The tool SHALL copy files that exist in source but not in target.

#### Scenario: New file addition

**Given** `notes/new-note.md` exists in backup  
**And** the file does not exist in target vault  
**When** sync executes  
**Then** the tool SHALL copy the file to target vault  
**And** SHALL preserve the file's relative path  
**And** SHALL log `[ADD] notes/new-note.md`

---

### Requirement: Update operation

The tool SHALL overwrite files when content has changed.

#### Scenario: Modified file update

**Given** `notes/modified.md` exists in both locations  
**And** hash of source differs from hash of target  
**When** sync executes  
**Then** the tool SHALL overwrite target with source content  
**And** SHALL log `[MOD] notes/modified.md (Hash mismatch)`

---

### Requirement: Skip operation

The tool SHALL skip files with identical content to preserve timestamps.

#### Scenario: Unchanged file preservation

**Given** `notes/unchanged.md` exists in both locations  
**And** hash of source equals hash of target  
**When** sync executes  
**Then** the tool SHALL NOT modify the target file  
**And** SHALL preserve the original modification timestamp  
**And** SHALL log `[SKIP] notes/unchanged.md`

---

### Requirement: Delete operation

The tool SHALL remove files that no longer exist in source.

#### Scenario: Deleted file removal

**Given** `notes/old-note.md` exists in target vault  
**And** the file does not exist in backup source  
**When** sync executes  
**Then** the tool SHALL delete the file from target vault  
**And** SHALL log `[DEL] notes/old-note.md`

---

### Requirement: Recursive directory synchronization

The tool SHALL process all files in nested directory structures.

#### Scenario: Deep directory structure

**Given** source contains `notes/projects/alpha/meeting.md`  
**When** sync executes  
**Then** the tool SHALL create necessary parent directories in target  
**And** SHALL apply sync logic to all files recursively  
**And** SHALL process both markdown files and asset files

---

### Requirement: Asset file handling

The tool SHALL apply the same hash-based sync logic to images and attachments.

#### Scenario: Image file synchronization

**Given** `images/diagram.png` exists in backup  
**When** hash comparison is performed  
**Then** the tool SHALL apply ADD/UPDATE/SKIP/DELETE logic  
**And** SHALL treat binary files identically to text files


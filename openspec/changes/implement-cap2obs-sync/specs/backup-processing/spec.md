# Spec: Backup Processing

## ADDED Requirements

### Requirement: ZIP file extraction

The tool SHALL extract Capacities backup ZIP files to a temporary workspace.

#### Scenario: Standard extraction

**Given** a valid backup ZIP file is selected  
**When** the tool begins processing  
**Then** it SHALL create a temporary directory `.temp_cap2obs/` in the working directory  
**And** SHALL extract all contents to this temporary location  
**And** SHALL validate extraction completed successfully

---

#### Scenario: Corrupted ZIP file

**Given** the backup file is corrupted or incomplete  
**When** extraction is attempted  
**Then** the tool SHALL catch the extraction error  
**And** SHALL log "ZIP extraction failed"  
**And** SHALL exit with code `4`

---

### Requirement: Content root detection

The tool SHALL locate the actual content directory within the extracted files.

#### Scenario: Nested vault structure

**Given** the ZIP contains structure `TopFolder/VaultName/notes/...`  
**When** extraction completes  
**Then** the tool SHALL detect `VaultName/` as the content root  
**And** SHALL use this as the sync source directory

---

#### Scenario: Flat structure

**Given** the ZIP directly contains `notes/` and `images/` folders  
**When** extraction completes  
**Then** the tool SHALL use the extraction root as content source

---

### Requirement: Filename pattern recognition

The tool SHALL parse filenames matching the Capacities backup format.

#### Scenario: Valid filename parsing

**Given** a file named `Capacities (2026-01-30 12-29-03).zip`  
**When** the tool parses the filename  
**Then** it SHALL extract date `2026-01-30`  
**And** SHALL extract time `12:29:03`

---

#### Scenario: Invalid filename format

**Given** a file named `backup-2026.zip`  
**When** the tool scans the directory  
**Then** it SHALL ignore this file  
**And** SHALL NOT include it in selection candidates

---

### Requirement: Temporary workspace cleanup

The tool SHALL ensure temporary files are removed after processing.

#### Scenario: Cleanup on success

**Given** sync completes successfully  
**When** the tool exits  
**Then** it SHALL recursively delete `.temp_cap2obs/`  
**And** SHALL NOT leave any temporary files

---

#### Scenario: Cleanup on failure

**Given** an error occurs during sync  
**When** the tool handles the error  
**Then** it SHALL still delete `.temp_cap2obs/` before exiting  
**And** SHALL log cleanup completion

---

#### Scenario: Cleanup on interruption

**Given** the user sends SIGINT (Ctrl+C)  
**When** the signal is received  
**Then** the tool SHALL cleanup temporary files  
**And** SHALL exit gracefully with code `6`

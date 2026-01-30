"""Sync engine with hash-based four-way logic (Add/Update/Skip/Delete)."""

import shutil
from pathlib import Path
from typing import Set
from dataclasses import dataclass
from cap2obs.logger import Logger
from cap2obs.hasher import compute_file_hash, files_are_identical


@dataclass
class SyncStats:
    """Statistics for sync operation."""
    added: int = 0
    modified: int = 0
    deleted: int = 0
    skipped: int = 0


class SyncEngine:
    """Hash-based synchronization engine."""
    
    def __init__(self, logger: Logger, dry_run: bool = False, vault_name: str = None):
        """
        Initialize sync engine.
        
        Args:
            logger: Logger instance
            dry_run: Whether to preview changes without applying them
            vault_name: Optional vault name for scoped logging
        """
        self.logger = logger
        self.dry_run = dry_run
        self.vault_name = vault_name
        self.stats = SyncStats()
    
    def sync(self, source_root: Path, target_root: Path) -> SyncStats:
        """
        Perform smart sync from source to target.
        
        Implements four-way logic:
        - ADD: File exists in source but not in target
        - UPDATE: File exists in both but content differs
        - SKIP: File exists in both with identical content
        - DELETE: File exists in target but not in source
        
        Args:
            source_root: Source directory (extracted backup)
            target_root: Target directory (Obsidian vault)
            
        Returns:
            SyncStats with operation counts
        """
        self.logger.info(f"Starting sync: {source_root} -> {target_root}")
        
        # Collect all files
        source_files = self._collect_files(source_root)
        target_files = self._collect_files(target_root)
        
        # Convert to relative paths for comparison
        source_relative = {f.relative_to(source_root) for f in source_files}
        target_relative = {f.relative_to(target_root) for f in target_files}
        
        # Process source files (ADD, UPDATE, SKIP)
        for rel_path in source_relative:
            source_file = source_root / rel_path
            target_file = target_root / rel_path
            
            if not target_file.exists():
                # ADD: New file
                self._add_file(source_file, target_file, str(rel_path))
            else:
                # UPDATE or SKIP based on hash
                if files_are_identical(source_file, target_file):
                    self._skip_file(str(rel_path))
                else:
                    self._update_file(source_file, target_file, str(rel_path))
        
        # Process target-only files (DELETE)
        files_to_delete = target_relative - source_relative
        for rel_path in sorted(files_to_delete):
            target_file = target_root / rel_path
            self._delete_file(target_file, str(rel_path))
        
        return self.stats
    
    def _collect_files(self, root: Path) -> Set[Path]:
        """
        Recursively collect all files in directory.
        
        Args:
            root: Root directory
            
        Returns:
            Set of file paths
        """
        files = set()
        if not root.exists():
            return files
        
        for item in root.rglob("*"):
            if item.is_file():
                files.add(item)
        
        return files
    
    def _add_file(self, source: Path, target: Path, rel_path: str):
        """Add new file to target."""
        self.logger.add(rel_path)
        
        if not self.dry_run:
            try:
                # Create parent directories if needed
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            except OSError as e:
                self.logger.error(f"Failed to add {rel_path}: {e}")
                raise
        
        self.stats.added += 1
    
    def _update_file(self, source: Path, target: Path, rel_path: str):
        """Update existing file in target."""
        self.logger.modify(rel_path, "Hash mismatch")
        
        if not self.dry_run:
            try:
                shutil.copy2(source, target)
            except OSError as e:
                self.logger.error(f"Failed to update {rel_path}: {e}")
                raise
        
        self.stats.modified += 1
    
    def _skip_file(self, rel_path: str):
        """Skip file with identical content."""
        self.logger.skip(rel_path)
        self.stats.skipped += 1
    
    def _delete_file(self, target: Path, rel_path: str):
        """Delete file from target."""
        self.logger.delete(rel_path)
        
        if not self.dry_run:
            try:
                target.unlink()
                
                # Clean up empty parent directories
                self._cleanup_empty_dirs(target.parent)
            except OSError as e:
                self.logger.error(f"Failed to delete {rel_path}: {e}")
                raise
        
        self.stats.deleted += 1
    
    def _cleanup_empty_dirs(self, directory: Path):
        """
        Recursively remove empty parent directories.
        
        Args:
            directory: Directory to check and potentially remove
        """
        try:
            # Don't remove the root target directory
            if not directory.exists() or not directory.is_dir():
                return
            
            # Check if empty
            if not any(directory.iterdir()):
                directory.rmdir()
                # Recursively check parent
                self._cleanup_empty_dirs(directory.parent)
        except OSError:
            # Ignore errors during cleanup
            pass

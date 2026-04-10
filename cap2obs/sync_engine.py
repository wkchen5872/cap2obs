"""Sync engine with hash-based four-way logic (Add/Update/Skip/Delete)."""

import shutil
from pathlib import Path
from typing import Dict, List, Set
from dataclasses import dataclass, field
from cap2obs.logger import Logger
from cap2obs.hasher import compute_file_hash, files_are_identical
from cap2obs.markdown_utils import inject_properties, parse_frontmatter, scan_markdown_index


# Files and directories starting with these prefixes will NEVER be deleted
# from the target, even if they don't exist in the source.
PROTECTED_PREFIXES = {
    ".obsidian",
    ".trash",
    ".git",
    ".smart-env",
    ".agents",
    ".claude",
    ".gemini",
    ".github",
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    ".DS_Store",
}

# Non-markdown file extensions that use hash-pool matching for rename detection.
MEDIA_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".rar", ".7z", ".tar", ".gz",
    ".mp3", ".mp4", ".wav", ".mov", ".avi",
}


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
        # Target paths claimed during source dispatch; exempt from deletion.
        self.retained_paths: Set[Path] = set()

    def sync(self, source_root: Path, target_root: Path) -> SyncStats:
        """
        Perform smart sync from source to target.

        Implements four-way logic per file type:
        - Markdown (.md): frontmatter cap2obs_source tracking
        - Media (MEDIA_EXTENSIONS): content-hash pool matching
        - Other files: path-based ADD/UPDATE/SKIP
        - DELETE: target-only files, respecting protected prefixes,
          retained paths, and managed markdown.

        Args:
            source_root: Source directory (extracted backup)
            target_root: Target directory (Obsidian vault)

        Returns:
            SyncStats with operation counts
        """
        self.retained_paths = set()
        self.stats = SyncStats()
        self.logger.info(f"Starting sync: {source_root} -> {target_root}")

        # Pre-scan target for hash pool (media) and MD index (markdown)
        hash_pool = self._build_target_hash_pool(target_root)
        md_index = self._build_target_md_index(target_root)

        # Collect all files
        source_files = self._collect_files(source_root)
        target_files = self._collect_files(target_root)

        source_relative = {f.relative_to(source_root) for f in source_files}
        target_relative = {f.relative_to(target_root) for f in target_files}

        # Process source files (ADD, UPDATE, SKIP)
        for rel_path in source_relative:
            source_file = source_root / rel_path
            target_file = target_root / rel_path

            if rel_path.suffix == ".md":
                self._sync_md_file(source_file, target_file, rel_path, target_root, md_index)
            elif self._is_media_file(rel_path):
                self._sync_media_file(source_file, target_file, rel_path, target_root, hash_pool)
            else:
                # Standard path-based logic for other file types
                if not target_file.exists():
                    self._add_file(source_file, target_file, str(rel_path))
                elif files_are_identical(source_file, target_file):
                    self._skip_file(str(rel_path))
                else:
                    self._update_file(source_file, target_file, str(rel_path))

        # Process target-only files (DELETE)
        files_to_delete = target_relative - source_relative
        safe_to_delete = []

        for rel_path in files_to_delete:
            if self._is_protected(str(rel_path)):
                continue
            if rel_path in self.retained_paths:
                continue
            # Protect managed markdown orphans; delete unmanaged orphans
            if rel_path.suffix == ".md":
                target_file = target_root / rel_path
                try:
                    content = target_file.read_text(encoding="utf-8")
                    props = parse_frontmatter(content)
                    if props.get("cap2obs_managed", "").lower() in ("true", "yes", "1"):
                        continue
                except (OSError, UnicodeDecodeError):
                    # Cannot read file — treat as protected rather than risk deleting it
                    continue
            safe_to_delete.append(rel_path)

        for rel_path in sorted(safe_to_delete):
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

    def _is_media_file(self, path: Path) -> bool:
        """
        Check if file uses hash-pool matching (non-markdown attachment).

        Args:
            path: File path (only suffix is examined)

        Returns:
            True if the file extension is in MEDIA_EXTENSIONS
        """
        return path.suffix.lower() in MEDIA_EXTENSIONS

    def _is_protected(self, rel_path: str) -> bool:
        """
        Check if a file path is protected from deletion.

        Args:
            rel_path: Relative path string

        Returns:
            True if path starts with any protected prefix
        """
        for prefix in PROTECTED_PREFIXES:
            if rel_path.startswith(prefix):
                return True
        return False

    def _build_target_hash_pool(self, target_root: Path) -> Dict[str, List[Path]]:
        """
        Hash all media files in target and return a hash → paths index.

        Used for content-based matching of renamed media files.

        Args:
            target_root: Target vault root directory

        Returns:
            Dict mapping MD5 hash → list of absolute target file paths
            (FIFO — pop(0) consumes one entry per source match)
        """
        pool: Dict[str, List[Path]] = {}
        for file_path in self._collect_files(target_root):
            if not self._is_media_file(file_path):
                continue
            try:
                h = compute_file_hash(file_path)
            except OSError:
                continue
            pool.setdefault(h, []).append(file_path)
        return pool

    def _build_target_md_index(self, target_root: Path) -> dict:
        """
        Scan target .md files for cap2obs_source and return an index.

        Args:
            target_root: Target vault root directory

        Returns:
            Dict mapping cap2obs_source → {"path": Path, "managed": bool}
        """
        return scan_markdown_index(target_root)

    def _sync_md_file(
        self,
        source: Path,
        target: Path,
        rel_path: Path,
        target_root: Path,
        md_index: dict,
    ) -> None:
        """
        Sync a single markdown file using frontmatter-based tracking.

        Args:
            source: Absolute source file path
            target: Expected target path (target_root / rel_path)
            rel_path: Relative path from source root
            target_root: Target vault root
            md_index: Index built by _build_target_md_index
        """
        source_id = source.stem

        if source_id in md_index:
            entry = md_index[source_id]
            target_md_path: Path = entry["path"]
            target_rel = target_md_path.relative_to(target_root)

            if entry["managed"]:
                # User has curated this note — do not overwrite
                self._skip_file(str(rel_path))
            else:
                try:
                    source_content = source.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError) as e:
                    self.logger.error(f"Failed to read {rel_path}: {e}")
                    return
                new_content = inject_properties(source_content, source_id)
                self._update_md_file(target_md_path, new_content, str(rel_path))

            self.retained_paths.add(target_rel)
        else:
            # Not in index: new file or legacy file at same path
            try:
                source_content = source.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as e:
                self.logger.error(f"Failed to read {rel_path}: {e}")
                return
            new_content = inject_properties(source_content, source_id)

            if target.exists():
                self._update_md_file(target, new_content, str(rel_path))
            else:
                self._add_md_file(target, new_content, str(rel_path))

    def _sync_media_file(
        self,
        source: Path,
        target: Path,
        rel_path: Path,
        target_root: Path,
        hash_pool: Dict[str, List[Path]],
    ) -> None:
        """
        Sync a single media file using hash-pool matching.

        Args:
            source: Absolute source file path
            target: Expected target path (target_root / rel_path)
            rel_path: Relative path from source root
            target_root: Target vault root
            hash_pool: Index built by _build_target_hash_pool
        """
        source_hash = compute_file_hash(source)

        if source_hash in hash_pool and hash_pool[source_hash]:
            # Content match found — consume one entry and retain it
            matched_target = hash_pool[source_hash].pop(0)
            self.retained_paths.add(matched_target.relative_to(target_root))
            self._skip_file(str(rel_path))
        elif target.exists():
            if files_are_identical(source, target):
                self._skip_file(str(rel_path))
            else:
                self._update_file(source, target, str(rel_path))
        else:
            self._add_file(source, target, str(rel_path))

    def _add_file(self, source: Path, target: Path, rel_path: str) -> None:
        """Add new file to target."""
        self.logger.add(rel_path)

        if not self.dry_run:
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            except OSError as e:
                self.logger.error(f"Failed to add {rel_path}: {e}")
                raise

        self.stats.added += 1

    def _add_md_file(self, target: Path, content: str, rel_path: str) -> None:
        """Add new markdown file with injected properties."""
        self.logger.add(rel_path)

        if not self.dry_run:
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            except OSError as e:
                self.logger.error(f"Failed to add {rel_path}: {e}")
                raise

        self.stats.added += 1

    def _update_file(self, source: Path, target: Path, rel_path: str) -> None:
        """Update existing file in target."""
        self.logger.modify(rel_path, "Hash mismatch")

        if not self.dry_run:
            try:
                shutil.copy2(source, target)
            except OSError as e:
                self.logger.error(f"Failed to update {rel_path}: {e}")
                raise

        self.stats.modified += 1

    def _update_md_file(self, target: Path, content: str, rel_path: str) -> None:
        """Update markdown file with injected properties."""
        self.logger.modify(rel_path, "Content updated")

        if not self.dry_run:
            try:
                target.write_text(content, encoding="utf-8")
            except OSError as e:
                self.logger.error(f"Failed to update {rel_path}: {e}")
                raise

        self.stats.modified += 1

    def _skip_file(self, rel_path: str) -> None:
        """Skip file with identical content."""
        self.logger.skip(rel_path)
        self.stats.skipped += 1

    def _delete_file(self, target: Path, rel_path: str) -> None:
        """Delete file from target."""
        self.logger.delete(rel_path)

        if not self.dry_run:
            try:
                target.unlink()
                self._cleanup_empty_dirs(target.parent)
            except OSError as e:
                self.logger.error(f"Failed to delete {rel_path}: {e}")
                raise

        self.stats.deleted += 1

    def _cleanup_empty_dirs(self, directory: Path) -> None:
        """
        Recursively remove empty parent directories.

        Args:
            directory: Directory to check and potentially remove
        """
        try:
            if not directory.exists() or not directory.is_dir():
                return
            if not any(directory.iterdir()):
                directory.rmdir()
                self._cleanup_empty_dirs(directory.parent)
        except OSError:
            pass

"""Backup file processing and extraction module."""

import re
import zipfile
import shutil
import signal
import atexit
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from cap2obs.logger import Logger


class BackupProcessor:
    """Handles Capacities backup file selection and extraction."""
    
    # Pattern: Capacities (2026-01-30 12-29-03).zip
    FILENAME_PATTERN = re.compile(r"Capacities \((\d{4}-\d{2}-\d{2}) (\d{2}-\d{2}-\d{2})\)\.zip")
    
    TEMP_DIR_NAME = ".temp_cap2obs"
    
    def __init__(self, backup_dir: Path, logger: Logger):
        """
        Initialize backup processor.
        
        Args:
            backup_dir: Directory containing backup ZIP files
            logger: Logger instance
        """
        self.backup_dir = backup_dir
        self.logger = logger
        self.temp_dir: Optional[Path] = None
        
        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals."""
        self.logger.info("Received interrupt signal, cleaning up...")
        self.cleanup()
        raise SystemExit(6)  # SYNC_ERROR
    
    def parse_filename(self, filename: str) -> Optional[tuple[datetime, str]]:
        """
        Parse Capacities backup filename.
        
        Args:
            filename: Backup filename
            
        Returns:
            Tuple of (datetime, original_filename) or None if invalid
        """
        match = self.FILENAME_PATTERN.match(filename)
        if not match:
            return None
        
        date_str, time_str = match.groups()
        time_str = time_str.replace("-", ":")
        dt_str = f"{date_str} {time_str}"
        
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            return (dt, filename)
        except ValueError:
            return None
    
    def find_backup_files(self) -> List[tuple[datetime, Path]]:
        """
        Find all valid Capacities backup files.
        
        Returns:
            List of (datetime, path) tuples sorted by datetime (newest first)
        """
        backups = []
        
        for file_path in self.backup_dir.glob("*.zip"):
            parsed = self.parse_filename(file_path.name)
            if parsed:
                dt, _ = parsed
                backups.append((dt, file_path))
        
        # Sort by datetime (newest first)
        backups.sort(reverse=True, key=lambda x: x[0])
        return backups
    
    def select_backup_file(
        self, 
        explicit_file: Optional[str] = None,
        target_date: Optional[str] = None
    ) -> Optional[Path]:
        """
        Select backup file based on priority strategy.
        
        Priority:
        1. explicit_file if provided
        2. target_date if provided (selects latest from that date)
        3. Auto-select newest overall
        
        Args:
            explicit_file: Specific filename to use
            target_date: Date string in YYYY-MM-DD format
            
        Returns:
            Path to selected backup file or None if not found
        """
        # Priority 1: Explicit file
        if explicit_file:
            file_path = self.backup_dir / explicit_file
            if file_path.exists():
                self.logger.info(f"Selected explicit file: {explicit_file}")
                return file_path
            else:
                self.logger.error(f"Specified file not found: {explicit_file}")
                return None
        
        # Find all valid backups
        backups = self.find_backup_files()
        
        if not backups:
            self.logger.error("No valid Capacities backup files found")
            return None
        
        # Priority 2: Date filter
        if target_date:
            try:
                target_dt = datetime.strptime(target_date, "%Y-%m-%d")
                date_filtered = [
                    (dt, path) for dt, path in backups
                    if dt.date() == target_dt.date()
                ]
                
                if not date_filtered:
                    self.logger.error(f"No backups found for date: {target_date}")
                    return None
                
                # Select latest from filtered list
                selected_dt, selected_path = date_filtered[0]
                self.logger.info(f"Selected backup from {target_date}: {selected_path.name}")
                return selected_path
            except ValueError:
                self.logger.error(f"Invalid date format: {target_date} (expected YYYY-MM-DD)")
                return None
        
        # Priority 3: Auto-select newest
        selected_dt, selected_path = backups[0]
        self.logger.info(f"Auto-selected newest backup: {selected_path.name}")
        return selected_path
    
    def extract_backup(self, backup_file: Path) -> Optional[Path]:
        """
        Extract backup ZIP to temporary directory.
        
        Args:
            backup_file: Path to ZIP file
            
        Returns:
            Path to extraction root directory (temp_dir) or None if extraction fails
        """
        # Create temporary directory
        self.temp_dir = self.backup_dir.parent / self.TEMP_DIR_NAME
        
        try:
            # Clean any existing temp dir
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Extracting {backup_file.name}...")
            
            with zipfile.ZipFile(backup_file, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            
            self.logger.info(f"Extraction complete: {self.temp_dir}")
            return self.temp_dir
            
        except zipfile.BadZipFile:
            self.logger.error(f"Corrupted ZIP file: {backup_file}")
            return None
        except OSError as e:
            self.logger.error(f"Extraction failed: {e}")
            return None
    
    def _find_content_root(self) -> Optional[Path]:
        """
        Locate the actual content directory within extracted files.
        
        Handles both:
        - Nested structure: TopFolder/VaultName/content/
        - Flat structure: content/ directly
        
        Returns:
            Path to content root or None if not found
        """
        if not self.temp_dir or not self.temp_dir.exists():
            return None
        
        # Check for direct content (flat structure)
        children = list(self.temp_dir.iterdir())
        
        if not children:
            return None
        
        # If only one subdirectory, it's likely the vault root
        if len(children) == 1 and children[0].is_dir():
            return children[0]
        
        # Otherwise use temp_dir itself as content root
        return self.temp_dir
    
    def cleanup(self):
        """Remove temporary extraction directory."""
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                self.logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
            except OSError as e:
                self.logger.warn(f"Failed to cleanup temp directory: {e}")
            finally:
                self.temp_dir = None

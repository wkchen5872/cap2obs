"""Logging module for Cap2Obs with structured output."""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO
from enum import Enum


class LogLevel(Enum):
    """Log level enumeration."""
    INFO = "INFO"
    ADD = "ADD"
    MOD = "MOD"
    SKIP = "SKIP"
    DEL = "DEL"
    WARN = "WARN"
    ERROR = "ERROR"


class Logger:
    """Structured logger with console and optional file output."""
    
    def __init__(self, log_file: Optional[Path] = None, dry_run: bool = False):
        """
        Initialize logger.
        
        Args:
            log_file: Optional path to log file
            dry_run: Whether running in dry-run mode (adds [DRY-RUN] prefix)
        """
        self.log_file = log_file
        self.dry_run = dry_run
        self._file_handle: Optional[TextIO] = None
        
        if self.log_file:
            try:
                # Create parent directories if needed
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
                self._file_handle = self.log_file.open("a", encoding="utf-8")
            except OSError as e:
                print(f"[WARN] Could not open log file {log_file}: {e}", file=sys.stderr)
    
    def _format_message(self, level: LogLevel, message: str) -> str:
        """
        Format log message with timestamp and level.
        
        Args:
            level: Log level
            message: Message text
            
        Returns:
            Formatted log entry
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = f"[DRY-RUN] " if self.dry_run and level in (LogLevel.ADD, LogLevel.MOD, LogLevel.DEL, LogLevel.SKIP) else ""
        return f"[{timestamp}] {prefix}[{level.value}] {message}"
    
    def _write(self, formatted_message: str, to_stderr: bool = False):
        """
        Write message to console and optionally to file.
        
        Args:
            formatted_message: Pre-formatted log message
            to_stderr: Whether to write to stderr instead of stdout
        """
        # Console output
        output = sys.stderr if to_stderr else sys.stdout
        print(formatted_message, file=output)
        
        # File output
        if self._file_handle:
            self._file_handle.write(formatted_message + "\n")
            self._file_handle.flush()
    
    def info(self, message: str):
        """Log informational message."""
        self._write(self._format_message(LogLevel.INFO, message))
    
    def add(self, file_path: str):
        """Log file addition."""
        message = f"Would add: {file_path}" if self.dry_run else file_path
        self._write(self._format_message(LogLevel.ADD, message))
    
    def modify(self, file_path: str, reason: str = "Hash mismatch"):
        """Log file modification."""
        message = f"Would modify: {file_path} ({reason})" if self.dry_run else f"{file_path} ({reason})"
        self._write(self._format_message(LogLevel.MOD, message))
    
    def skip(self, file_path: str):
        """Log file skip."""
        self._write(self._format_message(LogLevel.SKIP, file_path))
    
    def delete(self, file_path: str):
        """Log file deletion."""
        message = f"Would delete: {file_path}" if self.dry_run else file_path
        self._write(self._format_message(LogLevel.DEL, message))
    
    def warn(self, message: str):
        """Log warning message."""
        self._write(self._format_message(LogLevel.WARN, message), to_stderr=True)
    
    def error(self, message: str):
        """Log error message."""
        self._write(self._format_message(LogLevel.ERROR, message), to_stderr=True)
    
    def summary(self, added: int, modified: int, deleted: int, skipped: int):
        """
        Log execution summary.
        
        Args:
            added: Number of files added
            modified: Number of files modified
            deleted: Number of files deleted
            skipped: Number of files skipped
        """
        total = added + modified + deleted + skipped
        
        if added == 0 and modified == 0 and deleted == 0:
            self.info("SUCCESS: No changes detected")
        else:
            self.info(f"SUCCESS: {added} added, {modified} modified, {deleted} deleted ({total} files processed)")
    
    def close(self):
        """Close log file handle if open."""
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

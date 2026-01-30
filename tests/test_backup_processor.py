"""Tests for backup processor."""

import pytest
from datetime import datetime
from pathlib import Path
from cap2obs.backup_processor import BackupProcessor
from cap2obs.logger import Logger


def test_parse_filename_valid():
    """Test parsing valid Capacities backup filename."""
    logger = Logger()
    processor = BackupProcessor(Path("/tmp"), logger)
    
    result = processor.parse_filename("Capacities (2026-01-30 12-29-03).zip")
    assert result is not None
    
    dt, filename = result
    assert dt == datetime(2026, 1, 30, 12, 29, 3)
    assert filename == "Capacities (2026-01-30 12-29-03).zip"


def test_parse_filename_invalid():
    """Test parsing invalid filename."""
    logger = Logger()
    processor = BackupProcessor(Path("/tmp"), logger)
    
    result = processor.parse_filename("backup-2026.zip")
    assert result is None


def test_parse_filename_wrong_format():
    """Test parsing filename with wrong date format."""
    logger = Logger()
    processor = BackupProcessor(Path("/tmp"), logger)
    
    result = processor.parse_filename("Capacities (01-30-2026 12-29-03).zip")
    assert result is None

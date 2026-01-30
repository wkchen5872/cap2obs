"""Tests for vault detector module."""

import pytest
from pathlib import Path
from cap2obs.vault_detector import VaultDetector, StructureType
from cap2obs.logger import Logger


def test_detect_nested_structure(tmp_path):
    """Test detection of nested Capacities structure."""
    # Create nested structure
    wrapper = tmp_path / "Capacities (2026-01-30 12-29-03)"
    wrapper.mkdir()
    (wrapper / "Work").mkdir()
    (wrapper / "Personal").mkdir()
    (wrapper / "Work" / "note.md").touch()
    (wrapper / "Personal" / "note.md").touch()
    
    logger = Logger()
    detector = VaultDetector(tmp_path, logger)
    
    structure_type, vault_root = detector.detect_structure()
    
    assert structure_type == StructureType.NESTED
    assert vault_root == wrapper


def test_detect_flat_structure(tmp_path):
    """Test detection of flat structure."""
    # Create flat structure
    (tmp_path / "Work").mkdir()
    (tmp_path / "Personal").mkdir()
    (tmp_path / "Work" / "note.md").touch()
    (tmp_path / "Personal" / "note.md").touch()
    
    logger = Logger()
    detector = VaultDetector(tmp_path, logger)
    
    structure_type, vault_root = detector.detect_structure()
    
    assert structure_type == StructureType.FLAT
    assert vault_root == tmp_path


def test_find_vaults_nested(tmp_path):
    """Test finding vaults in nested structure."""
    wrapper = tmp_path / "Capacities (2026-01-30 12-29-03)"
    wrapper.mkdir()
    (wrapper / "Work").mkdir()
    (wrapper / "Personal").mkdir()
    (wrapper / "Work" / "note.md").touch()
    (wrapper / "Personal" / "note.md").touch()
    
    logger = Logger()
    detector = VaultDetector(tmp_path, logger)
    
    vaults = detector.find_vaults()
    
    assert len(vaults) == 2
    vault_names = [v.name for v in vaults]
    assert "Work" in vault_names
    assert "Personal" in vault_names


def test_find_vaults_excludes_hidden(tmp_path):
    """Test that hidden folders are excluded."""
    (tmp_path / "Work").mkdir()
    (tmp_path / ".hidden").mkdir()
    (tmp_path / "__MACOSX").mkdir()
    (tmp_path / "Work" / "note.md").touch()
    (tmp_path / ".hidden" / "file.txt").touch()
    (tmp_path / "__MACOSX" / "file.txt").touch()
    
    logger = Logger()
    detector = VaultDetector(tmp_path, logger)
    
    vaults = detector.find_vaults()
    
    assert len(vaults) == 1
    assert vaults[0].name == "Work"


def test_find_vaults_excludes_empty(tmp_path):
    """Test that empty vaults are excluded with warning."""
    (tmp_path / "Work").mkdir()
    (tmp_path / "Empty").mkdir()  # Empty folder
    (tmp_path / "Work" / "note.md").touch()
    
    logger = Logger()
    detector = VaultDetector(tmp_path, logger)
    
    vaults = detector.find_vaults()
    
    assert len(vaults) == 1
    assert vaults[0].name == "Work"

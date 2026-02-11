"""Tests for SyncEngine."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from cap2obs.sync_engine import SyncEngine


@pytest.fixture
def mock_logger():
    """Mock logger."""
    return Mock()


@pytest.fixture
def sync_engine(mock_logger):
    """SyncEngine fixture."""
    return SyncEngine(logger=mock_logger, dry_run=False)


def test_sync_deletes_unprotected_files(sync_engine, tmp_path):
    """Test that unprotected files are deleted."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    
    source.mkdir()
    target.mkdir()
    
    # Target has a file that source does not
    (target / "old_note.md").write_text("content")
    
    sync_engine.sync(source, target)
    
    assert not (target / "old_note.md").exists()
    sync_engine.logger.delete.assert_called_with("old_note.md")


def test_sync_preserves_protected_files(sync_engine, tmp_path):
    """Test that protected files are NOT deleted."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    
    source.mkdir()
    target.mkdir()
    
    # Target has protected config
    (target / ".obsidian").mkdir()
    (target / ".obsidian" / "config").write_text("config")
    
    sync_engine.sync(source, target)
    
    assert (target / ".obsidian" / "config").exists()
    # Should NOT have called delete for .obsidian/config
    # Note: The current implementation deletes recursively if a folder is removed,
    # or deletes individual files. The test expects the protection to work.
    
    # Verify no delete calls for protected paths
    for call in sync_engine.logger.delete.call_args_list:
        args, _ = call
        assert ".obsidian" not in args[0]


def test_sync_preserves_protected_directories(sync_engine, tmp_path):
    """Test that protected directories are preserved."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    
    source.mkdir()
    target.mkdir()
    
    # Target has .git directory
    git_dir = target / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("git config")
    
    sync_engine.sync(source, target)
    
    assert git_dir.exists()
    assert (git_dir / "config").exists()


def test_sync_preserves_prefix_matches(sync_engine, tmp_path):
    """Test that prefix matching works (e.g. .obsidian.mobile)."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    
    source.mkdir()
    target.mkdir()
    
    # Target has .obsidian.mobile
    mobile_dir = target / ".obsidian.mobile"
    mobile_dir.mkdir()
    (mobile_dir / "app.json").write_text("{}")
    
    sync_engine.sync(source, target)
    
    assert mobile_dir.exists()
    assert (mobile_dir / "app.json").exists()


def test_sync_mixed_content(sync_engine, tmp_path):
    """Test mixed content (protected and unprotected)."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    
    source.mkdir()
    target.mkdir()
    
    # Source has new note
    (source / "new.md").write_text("new")
    
    # Target has old note and protected config
    (target / "old.md").write_text("old")
    (target / ".trash").mkdir()
    (target / ".trash" / "deleted.md").write_text("trash")
    
    sync_engine.sync(source, target)
    
    # Check outcomes
    assert (target / "new.md").exists()      # Added
    assert not (target / "old.md").exists()  # Deleted
    assert (target / ".trash").exists()      # Protected

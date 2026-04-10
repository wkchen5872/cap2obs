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

    # Target has a file that source does not (no frontmatter → unmanaged)
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
    assert not (target / "old.md").exists()  # Deleted (no managed frontmatter)
    assert (target / ".trash").exists()      # Protected


# ---------------------------------------------------------------------------
# Hash pool tests (media rename tracking)
# ---------------------------------------------------------------------------

def test_hash_pool_skip_renamed_media(sync_engine, tmp_path):
    """Renamed media file with same hash is SKIP and the renamed file is retained."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    content = b"image bytes"
    (source / "original.png").write_bytes(content)
    # User renamed the file in Obsidian
    (target / "renamed.png").write_bytes(content)

    stats = sync_engine.sync(source, target)

    assert stats.skipped == 1
    assert stats.added == 0
    # Renamed file in target must NOT be deleted
    assert (target / "renamed.png").exists()
    # original.png must NOT be added to target
    assert not (target / "original.png").exists()


def test_hash_pool_add_when_no_match(sync_engine, tmp_path):
    """Truly new media file with no hash match is added normally."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    (source / "new_diagram.png").write_bytes(b"new image data")

    stats = sync_engine.sync(source, target)

    assert stats.added == 1
    assert (target / "new_diagram.png").exists()


def test_hash_pool_duplicate_media(sync_engine, tmp_path):
    """Two source files with same hash, one target match → one SKIP, one ADD."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    content = b"shared content"
    (source / "a.png").write_bytes(content)
    (source / "b.png").write_bytes(content)
    # Only one target file with same hash
    (target / "renamed.png").write_bytes(content)

    stats = sync_engine.sync(source, target)

    assert stats.skipped == 1
    assert stats.added == 1
    assert (target / "renamed.png").exists()


def test_retained_media_not_deleted(sync_engine, tmp_path):
    """Hash-matched (retained) media file is not deleted in the deletion phase."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    content = b"photo data"
    (source / "1BDD380D.jpg").write_bytes(content)
    # User renamed it
    (target / "curated_photo.jpg").write_bytes(content)

    sync_engine.sync(source, target)

    assert (target / "curated_photo.jpg").exists()
    assert not (target / "1BDD380D.jpg").exists()


# ---------------------------------------------------------------------------
# Markdown frontmatter tracking tests
# ---------------------------------------------------------------------------

def test_md_new_file_injects_properties(sync_engine, tmp_path):
    """New markdown file added with cap2obs properties injected."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    (source / "note.md").write_text("# My Note\nBody text.")

    sync_engine.sync(source, target)

    assert (target / "note.md").exists()
    content = (target / "note.md").read_text()
    assert 'cap2obs_source: "note"' in content
    assert "cap2obs_managed: false" in content
    assert "cap2obs_managed_date:" in content


def test_md_frontmatter_managed_skip(sync_engine, tmp_path):
    """Managed markdown (cap2obs_managed: true) is skipped — target not overwritten."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    (source / "note.md").write_text("# Source content")
    # Target has curated version at different name
    curated = (
        '---\n'
        'cap2obs_source: "note"\n'
        'cap2obs_managed: true\n'
        'cap2obs_managed_date: 2026-01-01\n'
        '---\n'
        '# Curated content\n'
    )
    (target / "curated_note.md").write_text(curated)

    stats = sync_engine.sync(source, target)

    assert stats.skipped == 1
    assert stats.modified == 0
    # Curated note must not be overwritten
    assert "Curated content" in (target / "curated_note.md").read_text()
    # Source note must not be added as a new file
    assert not (target / "note.md").exists()


def test_md_frontmatter_unmanaged_update(sync_engine, tmp_path):
    """Unmanaged markdown (cap2obs_managed: false) is updated with source content."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    (source / "note.md").write_text("# Updated source")
    unmanaged = (
        '---\n'
        'cap2obs_source: "note"\n'
        'cap2obs_managed: false\n'
        'cap2obs_managed_date:\n'
        '---\n'
        '# Old content\n'
    )
    (target / "my_note.md").write_text(unmanaged)

    stats = sync_engine.sync(source, target)

    assert stats.modified == 1
    updated = (target / "my_note.md").read_text()
    assert "Updated source" in updated
    assert 'cap2obs_source: "note"' in updated
    # Original file not added at source path
    assert not (target / "note.md").exists()


def test_orphan_managed_md_protected(sync_engine, tmp_path):
    """Orphan managed markdown (source removed) is protected from deletion."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    # Source does not have 'removed.md'
    curated = (
        '---\n'
        'cap2obs_source: "removed"\n'
        'cap2obs_managed: true\n'
        'cap2obs_managed_date: 2026-01-01\n'
        '---\n'
        '# Curated\n'
    )
    (target / "curated_note.md").write_text(curated)

    sync_engine.sync(source, target)

    assert (target / "curated_note.md").exists()
    sync_engine.logger.delete.assert_not_called()


def test_orphan_unmanaged_md_deleted(sync_engine, tmp_path):
    """Orphan unmanaged markdown (source removed) is deleted."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    old_note = (
        '---\n'
        'cap2obs_source: "old"\n'
        'cap2obs_managed: false\n'
        'cap2obs_managed_date:\n'
        '---\n'
        '# Old note\n'
    )
    (target / "old_note.md").write_text(old_note)

    sync_engine.sync(source, target)

    assert not (target / "old_note.md").exists()
    sync_engine.logger.delete.assert_called_once_with("old_note.md")


def test_non_media_non_md_files_standard_logic(sync_engine, tmp_path):
    """Non-.md, non-media files (e.g. .txt, .json) use standard path-based sync."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    # ADD: new .txt file
    (source / "notes.txt").write_text("hello")
    # SKIP: identical .json
    (source / "config.json").write_text('{"key": "value"}')
    (target / "config.json").write_text('{"key": "value"}')
    # UPDATE: changed .txt
    (source / "data.txt").write_text("new content")
    (target / "data.txt").write_text("old content")

    stats = sync_engine.sync(source, target)

    assert stats.added == 1
    assert stats.skipped == 1
    assert stats.modified == 1
    assert (target / "notes.txt").exists()
    assert (target / "notes.txt").read_text() == "hello"
    assert (target / "data.txt").read_text() == "new content"


def test_media_same_path_skip(sync_engine, tmp_path):
    """Media file at same path with identical hash is SKIP (no hash pool entry needed)."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    content = b"image data"
    (source / "photo.png").write_bytes(content)
    (target / "photo.png").write_bytes(content)

    stats = sync_engine.sync(source, target)

    assert stats.skipped == 1
    assert stats.modified == 0


def test_media_same_path_update(sync_engine, tmp_path):
    """Media file at same path with different hash is UPDATE."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    (source / "photo.png").write_bytes(b"new image")
    (target / "photo.png").write_bytes(b"old image")

    stats = sync_engine.sync(source, target)

    assert stats.modified == 1
    assert (target / "photo.png").read_bytes() == b"new image"

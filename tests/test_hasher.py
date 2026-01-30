"""Tests for hasher module."""

import pytest
import hashlib
from pathlib import Path
from cap2obs.hasher import compute_file_hash, files_are_identical


def test_compute_md5_hash(tmp_path):
    """Test MD5 hash computation."""
    test_file = tmp_path / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)
    
    expected_hash = hashlib.md5(content).hexdigest()
    computed_hash = compute_file_hash(test_file, algorithm="md5")
    
    assert computed_hash == expected_hash


def test_compute_sha256_hash(tmp_path):
    """Test SHA256 hash computation."""
    test_file = tmp_path / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)
    
    expected_hash = hashlib.sha256(content).hexdigest()
    computed_hash = compute_file_hash(test_file, algorithm="sha256")
    
    assert computed_hash == expected_hash


def test_files_are_identical_same_content(tmp_path):
    """Test identical file detection."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    
    content = b"Same content"
    file1.write_bytes(content)
    file2.write_bytes(content)
    
    assert files_are_identical(file1, file2) is True


def test_files_are_identical_different_content(tmp_path):
    """Test different file detection."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    
    file1.write_bytes(b"Content A")
    file2.write_bytes(b"Content B")
    
    assert files_are_identical(file1, file2) is False


def test_unsupported_algorithm_raises_error(tmp_path):
    """Test that unsupported algorithm raises ValueError."""
    test_file = tmp_path / "test.txt"
    test_file.write_bytes(b"test")
    
    with pytest.raises(ValueError, match="Unsupported hash algorithm"):
        compute_file_hash(test_file, algorithm="sha512")

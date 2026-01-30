"""Content hashing module for file comparison."""

import hashlib
from pathlib import Path
from typing import Union


def compute_file_hash(file_path: Path, algorithm: str = "md5", chunk_size: int = 8192) -> str:
    """
    Compute cryptographic hash of file content.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm ('md5' or 'sha256')
        chunk_size: Size of chunks to read (for memory efficiency)
        
    Returns:
        Hexadecimal hash string
        
    Raises:
        ValueError: If algorithm is not supported
        OSError: If file cannot be read
    """
    if algorithm == "md5":
        hasher = hashlib.md5()
    elif algorithm == "sha256":
        hasher = hashlib.sha256()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    with file_path.open("rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    
    return hasher.hexdigest()


def files_are_identical(path1: Path, path2: Path, algorithm: str = "md5") -> bool:
    """
    Check if two files have identical content via hash comparison.
    
    Args:
        path1: First file path
        path2: Second file path
        algorithm: Hash algorithm to use
        
    Returns:
        True if files have same content, False otherwise
    """
    try:
        hash1 = compute_file_hash(path1, algorithm)
        hash2 = compute_file_hash(path2, algorithm)
        return hash1 == hash2
    except OSError:
        return False

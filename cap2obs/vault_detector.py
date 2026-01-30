"""Vault detection module for multi-vault backup structure analysis."""

import re
from pathlib import Path
from typing import List, Tuple
from enum import Enum
from cap2obs.logger import Logger


class StructureType(Enum):
    """Backup structure type enumeration."""
    NESTED = "nested"  # Capacities (...)/Vault1, Vault2
    FLAT = "flat"      # Vault1, Vault2 directly


class VaultDetector:
    """Detects and lists vaults from extracted backup content."""
    
    # Pattern for Capacities wrapper folder: Capacities (2026-01-30 12-29-03)
    WRAPPER_PATTERN = re.compile(r"Capacities \(\d{4}-\d{2}-\d{2}")
    
    # Folders to exclude from vault detection
    EXCLUDED_PREFIXES = ('.', '__')
    
    def __init__(self, extraction_root: Path, logger: Logger):
        """
        Initialize vault detector.
        
        Args:
            extraction_root: Root path of extracted backup content
            logger: Logger instance
        """
        self.extraction_root = extraction_root
        self.logger = logger
    
    def detect_structure(self) -> Tuple[StructureType, Path]:
        """
        Detect backup structure type.
        
        Returns:
            Tuple of (structure_type, vault_root_path)
            - vault_root_path is where individual vault folders are located
        """
        top_level_items = list(self.extraction_root.iterdir())
        
        # Filter to directories only
        top_level_dirs = [d for d in top_level_items if d.is_dir()]
        
        if not top_level_dirs:
            self.logger.warn("No directories found in extracted backup")
            return (StructureType.FLAT, self.extraction_root)
        
        # Check if single folder matches Capacities wrapper pattern
        if len(top_level_dirs) == 1:
            folder_name = top_level_dirs[0].name
            if self.WRAPPER_PATTERN.match(folder_name):
                self.logger.info(f"Detected nested structure: {folder_name}")
                return (StructureType.NESTED, top_level_dirs[0])
        
        # Otherwise it's a flat structure
        self.logger.info("Detected flat structure")
        return (StructureType.FLAT, self.extraction_root)
    
    def find_vaults(self) -> List[Path]:
        """
        Find all vault folders in the extracted backup.
        
        Returns:
            List of paths to vault folders
        """
        structure_type, vault_root = self.detect_structure()
        
        vaults = []
        
        for item in vault_root.iterdir():
            # Skip files
            if not item.is_dir():
                continue
            
            # Skip hidden and system folders
            if any(item.name.startswith(prefix) for prefix in self.EXCLUDED_PREFIXES):
                self.logger.info(f"Skipping excluded folder: {item.name}")
                continue
            
            # Skip Capacities wrapper folders if we're in flat mode
            # (shouldn't happen but safety check)
            if self.WRAPPER_PATTERN.match(item.name):
                continue
            
            # Check if vault is empty
            if not any(item.iterdir()):
                self.logger.warn(f"Empty vault detected: {item.name}")
                continue
            
            vaults.append(item)
        
        # Sort alphabetically for consistent ordering
        vaults.sort(key=lambda p: p.name)
        
        if vaults:
            vault_names = [v.name for v in vaults]
            self.logger.info(f"Found {len(vaults)} vault(s): {', '.join(vault_names)}")
        else:
            self.logger.warn("No valid vaults found in backup")
        
        return vaults

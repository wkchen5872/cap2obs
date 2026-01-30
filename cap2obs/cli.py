"""Command-line interface for Cap2Obs."""

import argparse
import sys
from pathlib import Path
from cap2obs import __version__


class ExitCode:
    """Exit code constants for automation integration."""
    SUCCESS = 0
    BACKUP_DIR_ERROR = 1
    NO_FILE_FOUND = 2
    TARGET_ERROR = 3
    UNZIP_FAILED = 4
    PERMISSION_DENIED = 5
    SYNC_ERROR = 6


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog="cap2obs",
        description="Smart synchronization tool for Capacities backups to Obsidian vaults",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit Codes:
  0 - Success
  1 - Backup directory not found
  2 - No matching backup file found
  3 - Obsidian root path invalid
  4 - ZIP extraction failed
  5 - Permission denied
  6 - Unexpected sync error

Example:
  cap2obs --backup-dir /data/backups --obsidian-root /home/user/obsidian
  cap2obs --backup-dir /data/backups --obsidian-root /obsidian --date 2026-01-30
  cap2obs --backup-dir /data/backups --obsidian-root /obsidian --dry-run
        """
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    # Required arguments
    required = parser.add_argument_group("required arguments")
    required.add_argument(
        "--backup-dir",
        type=Path,
        required=True,
        metavar="PATH",
        help="Directory containing Capacities backup ZIP files"
    )
    required.add_argument(
        "--obsidian-root",
        type=Path,
        required=True,
        metavar="PATH",
        dest="obsidian_root",
        help="Root directory containing Obsidian vault folders"
    )
    
    # Backwards compatibility alias (deprecated)
    required.add_argument(
        "--obsidian-vault",
        type=Path,
        dest="obsidian_root",
        help=argparse.SUPPRESS  # Hide from help
    )
    
    # Optional arguments
    optional = parser.add_argument_group("optional arguments")
    optional.add_argument(
        "--date",
        type=str,
        metavar="YYYY-MM-DD",
        help="Sync specific backup date (auto-selects latest if multiple exist)"
    )
    optional.add_argument(
        "--file",
        type=str,
        metavar="FILENAME",
        help="Sync specific backup file (overrides --date)"
    )
    optional.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )
    optional.add_argument(
        "--log-file",
        type=Path,
        metavar="PATH",
        help="Write detailed logs to file"
    )
    optional.add_argument(
        "--keep-days",
        type=int,
        metavar="N",
        help="Delete backups older than N days after successful sync"
    )
    
    return parser


def validate_paths(backup_dir: Path, obsidian_root: Path) -> int:
    """
    Validate required directory paths.
    
    Returns:
        Exit code (0 if valid, error code otherwise)
    """
    if not backup_dir.exists():
        print(f"[ERROR] Backup directory not found: {backup_dir}", file=sys.stderr)
        return ExitCode.BACKUP_DIR_ERROR
    
    if not backup_dir.is_dir():
        print(f"[ERROR] Backup path is not a directory: {backup_dir}", file=sys.stderr)
        return ExitCode.BACKUP_DIR_ERROR
    
    if not obsidian_root.exists():
        print(f"[ERROR] Obsidian root not found: {obsidian_root}", file=sys.stderr)
        return ExitCode.TARGET_ERROR
    
    if not obsidian_root.is_dir():
        print(f"[ERROR] Obsidian root is not a directory: {obsidian_root}", file=sys.stderr)
        return ExitCode.TARGET_ERROR
    
    return ExitCode.SUCCESS


def cleanup_old_backups(backup_dir: Path, keep_days: int, logger):
    """
    Delete backup files older than specified days.
    
    Args:
        backup_dir: Directory containing backups
        keep_days: Number of days to keep
        logger: Logger instance
    """
    from datetime import datetime, timedelta
    from cap2obs.backup_processor import BackupProcessor
    
    cutoff_date = datetime.now() - timedelta(days=keep_days)
    processor = BackupProcessor(backup_dir, logger)
    backups = processor.find_backup_files()
    
    deleted_count = 0
    for backup_dt, backup_path in backups:
        if backup_dt < cutoff_date:
            try:
                backup_path.unlink()
                logger.info(f"Deleted old backup: {backup_path.name}")
                deleted_count += 1
            except OSError as e:
                logger.warn(f"Failed to delete {backup_path.name}: {e}")
    
    if deleted_count > 0:
        logger.info(f"Cleanup complete: {deleted_count} old backup(s) removed")


def main() -> int:
    """Main entry point for CLI."""
    from cap2obs.logger import Logger
    from cap2obs.backup_processor import BackupProcessor
    from cap2obs.sync_engine import SyncEngine
    
    parser = create_parser()
    args = parser.parse_args()
    
    # Validate required paths
    exit_code = validate_paths(args.backup_dir, args.obsidian_root)
    if exit_code != ExitCode.SUCCESS:
        return exit_code
    
    # Initialize logger
    with Logger(log_file=args.log_file, dry_run=args.dry_run) as logger:
        try:
            # Check for deprecated parameter usage (via CLI inspection)
            if '--obsidian-vault' in sys.argv:
                logger.warn("--obsidian-vault is deprecated, use --obsidian-root instead")
            
            logger.info(f"Cap2Obs v{__version__} started")
            logger.info(f"Backup directory: {args.backup_dir}")
            logger.info(f"Obsidian root: {args.obsidian_root}")
            
            if args.dry_run:
                logger.info("Running in DRY-RUN mode")
            
            # Initialize backup processor
            processor = BackupProcessor(args.backup_dir, logger)
            
            # Select backup file
            backup_file = processor.select_backup_file(
                explicit_file=args.file,
                target_date=args.date
            )
            
            if not backup_file:
                return ExitCode.NO_FILE_FOUND
            
            # Extract backup
            extraction_root = processor.extract_backup(backup_file)
            
            if not extraction_root:
                processor.cleanup()
                return ExitCode.UNZIP_FAILED
            
            # Detect vaults in backup
            from cap2obs.vault_detector import VaultDetector
            from cap2obs.sync_engine import SyncStats
            
            detector = VaultDetector(extraction_root, logger)
            vaults = detector.find_vaults()
            
            if not vaults:
                logger.error("No vaults found in backup")
                processor.cleanup()
                return ExitCode.NO_FILE_FOUND
            
            # Initialize aggregate stats
            total_stats = SyncStats()
            failed_vaults = []
            
            # Sync each vault
            for vault_path in vaults:
                vault_name = vault_path.name
                target_vault = args.obsidian_root / vault_name
                
                try:
                    # Create target folder if missing
                    if not target_vault.exists():
                        if not args.dry_run:
                            target_vault.mkdir(parents=True, exist_ok=True)
                        logger.info(f"[{vault_name}] Creating new vault folder")
                    
                    # Initialize sync engine for this vault
                    sync_engine = SyncEngine(logger, dry_run=args.dry_run, vault_name=vault_name)
                    
                    # Perform sync
                    logger.info(f"[{vault_name}] Starting synchronization...")
                    stats = sync_engine.sync(vault_path, target_vault)
                    
                    # Log per-vault summary
                    logger.info(f"[{vault_name}] Completed: {stats.added} added, {stats.modified} modified, {stats.deleted} deleted")
                    
                    # Aggregate stats
                    total_stats.added += stats.added
                    total_stats.modified += stats.modified
                    total_stats.deleted += stats.deleted
                    total_stats.skipped += stats.skipped
                    
                except PermissionError as e:
                    logger.error(f"[{vault_name}] Permission denied: {e}")
                    failed_vaults.append(vault_name)
                except OSError as e:
                    logger.error(f"[{vault_name}] Sync failed: {e}")
                    failed_vaults.append(vault_name)
            
            # Log final summary
            vault_count = len(vaults)
            if failed_vaults:
                logger.info(f"PARTIAL SUCCESS: {vault_count - len(failed_vaults)}/{vault_count} vaults synced "
                           f"({total_stats.added} added, {total_stats.modified} modified, {total_stats.deleted} deleted)")
                logger.warn(f"Failed vaults: {', '.join(failed_vaults)}")
            else:
                logger.info(f"SUCCESS: {vault_count} vault(s) synced "
                           f"({total_stats.added} added, {total_stats.modified} modified, {total_stats.deleted} deleted)")
            
            # Cleanup temporary files
            processor.cleanup()
            
            # Optional: cleanup old backups
            if args.keep_days and not args.dry_run:
                logger.info(f"Cleaning up backups older than {args.keep_days} days...")
                cleanup_old_backups(args.backup_dir, args.keep_days, logger)
            
            # Return appropriate exit code
            if failed_vaults:
                return ExitCode.SYNC_ERROR
            return ExitCode.SUCCESS
            
        except PermissionError as e:
            logger.error(f"Permission denied: {e}")
            return ExitCode.PERMISSION_DENIED
        except OSError as e:
            logger.error(f"I/O error: {e}")
            return ExitCode.SYNC_ERROR
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return ExitCode.SYNC_ERROR


if __name__ == "__main__":
    sys.exit(main())

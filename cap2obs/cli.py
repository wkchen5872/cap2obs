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
  3 - Obsidian vault path invalid
  4 - ZIP extraction failed
  5 - Permission denied
  6 - Unexpected sync error

Example:
  cap2obs --backup-dir /data/backups --obsidian-vault /home/user/vault
  cap2obs --backup-dir /data/backups --obsidian-vault /vault --date 2026-01-30
  cap2obs --backup-dir /data/backups --obsidian-vault /vault --dry-run
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
        "--obsidian-vault",
        type=Path,
        required=True,
        metavar="PATH",
        help="Target Obsidian vault directory"
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


def validate_paths(backup_dir: Path, vault_dir: Path) -> int:
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
    
    if not vault_dir.exists():
        print(f"[ERROR] Obsidian vault not found: {vault_dir}", file=sys.stderr)
        return ExitCode.TARGET_ERROR
    
    if not vault_dir.is_dir():
        print(f"[ERROR] Vault path is not a directory: {vault_dir}", file=sys.stderr)
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
    exit_code = validate_paths(args.backup_dir, args.obsidian_vault)
    if exit_code != ExitCode.SUCCESS:
        return exit_code
    
    # Initialize logger
    with Logger(log_file=args.log_file, dry_run=args.dry_run) as logger:
        try:
            logger.info(f"Cap2Obs v{__version__} started")
            logger.info(f"Backup directory: {args.backup_dir}")
            logger.info(f"Obsidian vault: {args.obsidian_vault}")
            
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
            content_root = processor.extract_backup(backup_file)
            
            if not content_root:
                processor.cleanup()
                return ExitCode.UNZIP_FAILED
            
            # Initialize sync engine
            sync_engine = SyncEngine(logger, dry_run=args.dry_run)
            
            # Perform sync
            logger.info("Starting synchronization...")
            stats = sync_engine.sync(content_root, args.obsidian_vault)
            
            # Log summary
            logger.summary(stats.added, stats.modified, stats.deleted, stats.skipped)
            
            # Cleanup temporary files
            processor.cleanup()
            
            # Optional: cleanup old backups
            if args.keep_days and not args.dry_run:
                logger.info(f"Cleaning up backups older than {args.keep_days} days...")
                cleanup_old_backups(args.backup_dir, args.keep_days, logger)
            
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

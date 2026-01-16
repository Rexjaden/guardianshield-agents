#!/usr/bin/env python3
"""
GuardianShield Cache Cleanup System
Optimizes memory and RAM by cleaning cached data and temporary files.
"""

import os
import sys
import json
import shutil
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import gzip

class CacheCleanupManager:
    """Manages cache cleanup operations for the GuardianShield system."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.cleanup_report = {
            'timestamp': datetime.now().isoformat(),
            'files_cleaned': [],
            'space_freed': 0,
            'databases_optimized': [],
            'logs_archived': [],
            'errors': []
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('cache_cleanup.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes."""
        try:
            return file_path.stat().st_size if file_path.exists() else 0
        except Exception:
            return 0
    
    def format_size(self, size_bytes: int) -> str:
        """Format bytes to human readable string."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def clean_python_cache(self):
        """Remove Python cache files and directories."""
        self.logger.info("Cleaning Python cache files...")
        
        cache_patterns = [
            '**/__pycache__',
            '**/*.pyc',
            '**/*.pyo',
            '**/*.pyd',
            '**/.pytest_cache',
            '**/pytest_cache'
        ]
        
        for pattern in cache_patterns:
            for path in self.project_root.glob(pattern):
                try:
                    size_before = self.get_file_size(path)
                    if path.is_dir():
                        shutil.rmtree(path)
                        self.logger.info(f"Removed directory: {path}")
                    else:
                        path.unlink()
                        self.logger.info(f"Removed file: {path}")
                    
                    self.cleanup_report['files_cleaned'].append(str(path))
                    self.cleanup_report['space_freed'] += size_before
                except Exception as e:
                    self.cleanup_report['errors'].append(f"Error removing {path}: {str(e)}")
                    self.logger.error(f"Error removing {path}: {str(e)}")
    
    def archive_old_logs(self, days_old: int = 7):
        """Archive log files older than specified days."""
        self.logger.info(f"Archiving logs older than {days_old} days...")
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        log_files = list(self.project_root.glob('**/*.log')) + list(self.project_root.glob('**/*.jsonl'))
        
        for log_file in log_files:
            try:
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    # Create compressed archive
                    archive_name = f"{log_file.stem}_{datetime.fromtimestamp(log_file.stat().st_mtime).strftime('%Y%m%d')}.gz"
                    archive_path = log_file.parent / 'archives' / archive_name
                    
                    # Create archives directory if it doesn't exist
                    archive_path.parent.mkdir(exist_ok=True)
                    
                    # Compress and archive
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(archive_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    size_freed = self.get_file_size(log_file)
                    log_file.unlink()
                    
                    self.cleanup_report['logs_archived'].append({
                        'original': str(log_file),
                        'archived_to': str(archive_path),
                        'size_freed': size_freed
                    })
                    self.cleanup_report['space_freed'] += size_freed
                    self.logger.info(f"Archived: {log_file} -> {archive_path}")
                    
            except Exception as e:
                self.cleanup_report['errors'].append(f"Error archiving {log_file}: {str(e)}")
                self.logger.error(f"Error archiving {log_file}: {str(e)}")
    
    def optimize_databases(self):
        """Optimize SQLite databases to reclaim space."""
        self.logger.info("Optimizing SQLite databases...")
        
        db_files = list(self.project_root.glob('**/*.db'))
        
        for db_file in db_files:
            try:
                size_before = self.get_file_size(db_file)
                
                # Connect and optimize
                conn = sqlite3.connect(str(db_file))
                conn.execute('VACUUM')
                conn.execute('PRAGMA optimize')
                conn.close()
                
                size_after = self.get_file_size(db_file)
                space_saved = size_before - size_after
                
                self.cleanup_report['databases_optimized'].append({
                    'database': str(db_file),
                    'size_before': size_before,
                    'size_after': size_after,
                    'space_saved': space_saved
                })
                self.cleanup_report['space_freed'] += space_saved
                
                self.logger.info(f"Optimized {db_file}: saved {self.format_size(space_saved)}")
                
            except Exception as e:
                self.cleanup_report['errors'].append(f"Error optimizing {db_file}: {str(e)}")
                self.logger.error(f"Error optimizing {db_file}: {str(e)}")
    
    def clean_temporary_files(self):
        """Remove temporary files and directories."""
        self.logger.info("Cleaning temporary files...")
        
        temp_patterns = [
            '**/*.tmp',
            '**/*.temp',
            '**/.tmp',
            '**/temp',
            '**/*.bak',
            '**/*.backup',
            '**/*~',
            '**/.DS_Store'
        ]
        
        for pattern in temp_patterns:
            for path in self.project_root.glob(pattern):
                try:
                    size_before = self.get_file_size(path)
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    
                    self.cleanup_report['files_cleaned'].append(str(path))
                    self.cleanup_report['space_freed'] += size_before
                    self.logger.info(f"Removed temp file: {path}")
                    
                except Exception as e:
                    self.cleanup_report['errors'].append(f"Error removing temp file {path}: {str(e)}")
                    self.logger.error(f"Error removing temp file {path}: {str(e)}")
    
    def clean_agent_memory_caches(self):
        """Clean agent-specific memory caches and temporary data."""
        self.logger.info("Cleaning agent memory caches...")
        
        # Look for memory dump files, temporary session data, etc.
        cache_patterns = [
            '**/agent_*_cache.json',
            '**/session_*.tmp',
            '**/memory_dump_*.json',
            '**/*.memory',
            '**/active_sessions.encrypted'  # If it's a cache file
        ]
        
        for pattern in cache_patterns:
            for path in self.project_root.glob(pattern):
                try:
                    # Check if it's actually a cache file (not permanent storage)
                    if self.is_cache_file(path):
                        size_before = self.get_file_size(path)
                        path.unlink()
                        
                        self.cleanup_report['files_cleaned'].append(str(path))
                        self.cleanup_report['space_freed'] += size_before
                        self.logger.info(f"Removed agent cache: {path}")
                        
                except Exception as e:
                    self.cleanup_report['errors'].append(f"Error removing agent cache {path}: {str(e)}")
                    self.logger.error(f"Error removing agent cache {path}: {str(e)}")
    
    def is_cache_file(self, path: Path) -> bool:
        """Determine if a file is safe to delete as cache."""
        # Add logic to identify cache files vs important data
        cache_indicators = [
            'cache',
            'temp',
            'tmp',
            '_dump_',
            'session_'
        ]
        
        filename_lower = path.name.lower()
        return any(indicator in filename_lower for indicator in cache_indicators)
    
    def run_cleanup(self, archive_logs: bool = True, optimize_db: bool = True):
        """Run the complete cleanup process."""
        self.logger.info("Starting GuardianShield cache cleanup...")
        
        try:
            # Clean Python cache
            self.clean_python_cache()
            
            # Clean temporary files
            self.clean_temporary_files()
            
            # Clean agent memory caches
            self.clean_agent_memory_caches()
            
            # Archive old logs if requested
            if archive_logs:
                self.archive_old_logs()
            
            # Optimize databases if requested
            if optimize_db:
                self.optimize_databases()
            
            # Generate report
            self.generate_report()
            
            self.logger.info("Cache cleanup completed successfully!")
            self.logger.info(f"Total space freed: {self.format_size(self.cleanup_report['space_freed'])}")
            
        except Exception as e:
            self.logger.error(f"Cache cleanup failed: {str(e)}")
            self.cleanup_report['errors'].append(f"General cleanup error: {str(e)}")
    
    def generate_report(self):
        """Generate cleanup report."""
        report_file = self.project_root / f"cache_cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.cleanup_report, f, indent=2, default=str)
        
        self.logger.info(f"Cleanup report saved to: {report_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("GUARDIANSHIELD CACHE CLEANUP SUMMARY")
        print("="*60)
        print(f"Files cleaned: {len(self.cleanup_report['files_cleaned'])}")
        print(f"Databases optimized: {len(self.cleanup_report['databases_optimized'])}")
        print(f"Logs archived: {len(self.cleanup_report['logs_archived'])}")
        print(f"Total space freed: {self.format_size(self.cleanup_report['space_freed'])}")
        print(f"Errors encountered: {len(self.cleanup_report['errors'])}")
        print("="*60)


def main():
    """Main entry point for cache cleanup."""
    cleanup_manager = CacheCleanupManager()
    
    # Parse command line arguments
    archive_logs = '--no-archive' not in sys.argv
    optimize_db = '--no-optimize' not in sys.argv
    
    # Run cleanup
    cleanup_manager.run_cleanup(archive_logs=archive_logs, optimize_db=optimize_db)


if __name__ == "__main__":
    main()
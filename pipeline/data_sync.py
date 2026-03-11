"""Data synchronization and backup."""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import logging

logger = logging.getLogger(__name__)


class DataSync:
    """Sync and backup data files."""
    
    def __init__(self, raw_dir: str = 'data/raw', 
                 processed_dir: str = 'data/processed',
                 backup_dir: str = 'data/backup'):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.backup_dir = Path(backup_dir)
        
        for d in [self.raw_dir, self.processed_dir, self.backup_dir]:
            d.mkdir(parents=True, exist_ok=True)
    
    def backup_daily(self):
        """Create daily backup of processed data."""
        date_str = datetime.now().strftime('%Y%m%d')
        backup_path = self.backup_dir / date_str
        backup_path.mkdir(exist_ok=True)
        
        # Copy processed files
        for f in self.processed_dir.glob('*.csv'):
            shutil.copy(f, backup_path / f.name)
            logger.info(f"Backed up: {f.name}")
        
        return backup_path
    
    def cleanup_old_backups(self, days: int = 30):
        """Remove backups older than N days."""
        cutoff = datetime.now() - timedelta(days=days)
        
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                try:
                    dir_date = datetime.strptime(backup_dir.name, '%Y%m%d')
                    if dir_date < cutoff:
                        shutil.rmtree(backup_dir)
                        logger.info(f"Removed old backup: {backup_dir.name}")
                except ValueError:
                    continue  # Not a date-formatted directory
    
    def consolidate_regime_history(self, market: str) -> pd.DataFrame:
        """Combine all historical regime classifications."""
        files = list(self.processed_dir.glob(f'{market}_regime_*.csv'))
        
        if not files:
            logger.warning(f"No history files for {market}")
            return pd.DataFrame()
        
        dfs = [pd.read_csv(f) for f in sorted(files)]
        combined = pd.concat(dfs, ignore_index=True)
        combined['date'] = pd.to_datetime(combined['date'])
        
        # Remove duplicates
        combined = combined.drop_duplicates(subset=['date'], keep='last')
        
        return combined.sort_values('date')


def sync_data():
    """Run data sync."""
    sync = DataSync()
    sync.backup_daily()
    sync.cleanup_old_backups(days=30)
    logger.info("Data sync complete")


if __name__ == "__main__":
    sync_data()

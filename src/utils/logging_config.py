"""Logging configuration."""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(log_dir: str = 'data/logs', 
                  level: int = logging.INFO) -> logging.Logger:
    """
    Setup logging to file and console.
    
    Args:
        log_dir: Directory for log files
        level: Logging level
    
    Returns:
        Logger instance
    """
    # Create log directory
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Log file with date
    log_file = Path(log_dir) / f"regime_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger

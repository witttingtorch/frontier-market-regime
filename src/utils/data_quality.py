"""Data quality checks."""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional


def validate_data(df: pd.DataFrame, 
                  required_columns: list,
                  date_column: str = 'date') -> Dict:
    """
    Validate dataframe quality.
    
    Returns:
        Dict with 'valid' (bool) and 'issues' (list)
    """
    issues = []
    
    # Check empty
    if df.empty:
        issues.append("Dataframe is empty")
        return {'valid': False, 'issues': issues}
    
    # Check required columns
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        issues.append(f"Missing columns: {missing}")
    
    # Check for NaN values
    nan_count = df.isna().sum().sum()
    if nan_count > 0:
        issues.append(f"Contains {nan_count} NaN values")
    
    # Check date range
    if date_column in df.columns:
        latest = pd.to_datetime(df[date_column]).max()
        age = (datetime.now() - latest).days
        if age > 7:
            issues.append(f"Data is {age} days old")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'rows': len(df),
        'columns': list(df.columns)
    }


def check_data_freshness(last_update: datetime, 
                         max_age_hours: int = 24) -> bool:
    """Check if data is fresh enough."""
    if last_update is None:
        return False
    age = datetime.now() - last_update
    return age < timedelta(hours=max_age_hours)

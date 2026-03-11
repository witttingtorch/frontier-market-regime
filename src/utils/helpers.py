"""General helper functions."""

import pandas as pd
from datetime import datetime, timedelta


def resample_to_business_days(df: pd.DataFrame, 
                               date_col: str = 'date') -> pd.DataFrame:
    """Resample dataframe to business days, forward fill."""
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col)
    df = df.resample('B').last().ffill()
    return df.reset_index()


def calculate_z_score(series: pd.Series, 
                      window: int = 252) -> pd.Series:
    """Calculate rolling Z-score."""
    mean = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    return (series - mean) / std


def format_currency(value: float, currency: str = 'USD') -> str:
    """Format number as currency string."""
    if currency == 'KES':
        return f"KSh {value:,.2f}"
    elif currency == 'AZN':
        return f"₼ {value:,.2f}"
    else:
        return f"${value:,.2f}M" if abs(value) > 1e6 else f"${value:,.2f}"

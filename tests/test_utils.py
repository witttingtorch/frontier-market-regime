"""Test utilities."""

import sys
sys.path.insert(0, 'src')

from utils import validate_data, setup_logging, format_currency
import pandas as pd
from datetime import datetime

# Test logging
logger = setup_logging()
logger.info("Testing utils")

# Test data validation
df = pd.DataFrame({
    'date': [datetime.now()],
    'rate': [130.5],
    'volume': [1000]
})

result = validate_data(df, ['date', 'rate', 'volume'])
print(f"\nValidation: {result}")

# Test currency formatting
print(f"\nKES: {format_currency(157.25, 'KES')}")
print(f"AZN: {format_currency(1.70, 'AZN')}")
print(f"USD: {format_currency(8500000, 'USD')}")

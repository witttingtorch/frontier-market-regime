import sys
sys.path.insert(0, 'src')

from config import MARKETS, DATA_DIR, RAW_DIR
from config import MarketConfig

print("=" * 60)
print("TESTING CONFIG")
print("=" * 60)

# Test markets
for key, market in MARKETS.items():
    print(f"\n{key.upper()}:")
    print(f"  Name: {market.name}")
    print(f"  Currency: {market.currency_pair}")
    print(f"  Central Bank: {market.central_bank}")
    print(f"  FX Thresholds: {market.fx_vol_threshold_green:.0%} / {market.fx_vol_threshold_red:.0%}")

# Test paths
print(f"\nDirectories:")
print(f"  DATA_DIR: {DATA_DIR}")
print(f"  RAW_DIR: {RAW_DIR}")

print("\n✅ Config loaded successfully!")

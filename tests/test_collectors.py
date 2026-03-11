"""Test all data collectors."""

import sys
sys.path.insert(0, 'src')

from collectors.cba_collector import CBACollector
from collectors.cbk_collector import CBKCollector
from collectors.nse_collector import NSECollector

print("=" * 60)
print("TESTING CBA (Azerbaijan)")
print("=" * 60)
cba = CBACollector()
cba_rates = cba.get_usd_history(days=5)
print(cba_rates[['currency', 'azn_per_unit']].tail())

print("\n" + "=" * 60)
print("TESTING CBK (Kenya)")
print("=" * 60)
cbk = CBKCollector()
cbk_rates = cbk.get_rates(currency='USD')
print(cbk_rates[['date', 'kes_per_usd']].tail())

print("\n" + "=" * 60)
print("TESTING NSE (RapidAPI — may fail if not subscribed)")
print("=" * 60)
nse = NSECollector()
nse_stocks = nse.get_all_stocks()
print(f"Stocks found: {len(nse_stocks)}")
if not nse_stocks.empty:
    print(nse_stocks[['symbol', 'name']].head())

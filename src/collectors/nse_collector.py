"""Nairobi Securities Exchange collector."""

import requests
import pandas as pd
import numpy as np
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class NSECollector:
    """NSE RapidAPI client — requires API key."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('RAPIDAPI_KEY')
        if not self.api_key:
            logger.warning("No RapidAPI key — NSE collector disabled")

        self.session = requests.Session()
        self.session.headers.update({
            'X-RapidAPI-Key': self.api_key or '',
            'X-RapidAPI-Host': 'nairobi-stock-exchange-nse.p.rapidapi.com'
        })
        self.base_url = "https://nairobi-stock-exchange-nse.p.rapidapi.com"

    def get_all_stocks(self) -> pd.DataFrame:
        """Get all NSE stocks."""
        if not self.api_key:
            logger.error("Cannot fetch stocks — no API key")
            return pd.DataFrame()
        try:
            response = self.session.get(f"{self.base_url}/stocks", timeout=10)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                df = pd.DataFrame(data)
                logger.info(f"NSE: Fetched {len(df)} stocks")
                return df
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"NSE Error: {e}")
            return pd.DataFrame()

    def get_stock(self, symbol: str) -> dict:
        """Get specific stock quote."""
        if not self.api_key:
            return {}
        try:
            response = self.session.get(
                f"{self.base_url}/stock/{symbol}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"NSE Error fetching {symbol}: {e}")
            return {}

    def get_market_summary(self) -> dict:
        """Get NSE market summary — index level, volume, turnover."""
        if not self.api_key:
            return {}
        try:
            response = self.session.get(
                f"{self.base_url}/market_summary",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"NSE market summary error: {e}")
            return {}

    def calculate_capital_flow_signal(self) -> dict:
        """
        Derive capital flow signal from NSE market data.

        Uses market turnover and price momentum as a proxy for
        net foreign investor flows — since direct foreign flow
        data is not available via this API.

        Returns:
            dict with flow_z (Z-score proxy) and interpretation
        """
        stocks = self.get_all_stocks()

        if stocks.empty:
            logger.warning("No stock data — returning neutral flow signal")
            return {
                'flow_z': 0.0,
                'flow_usd': 0.0,
                'interpretation': 'No data — neutral assumption',
                'source': 'NSE_UNAVAILABLE'
            }

        try:
            # Look for price change and volume columns
            price_col = next(
                (c for c in ['change', 'price_change', 'pct_change', 'change_pct']
                 if c in stocks.columns), None
            )
            volume_col = next(
                (c for c in ['volume', 'shares_traded', 'turnover']
                 if c in stocks.columns), None
            )

            if price_col and volume_col:
                # Convert to numeric safely
                stocks[price_col] = pd.to_numeric(stocks[price_col], errors='coerce')
                stocks[volume_col] = pd.to_numeric(stocks[volume_col], errors='coerce')
                stocks = stocks.dropna(subset=[price_col, volume_col])

                # Price momentum signal — weighted by volume
                avg_change = np.average(
                    stocks[price_col],
                    weights=stocks[volume_col]
                )

                # Convert to Z-score proxy
                # Assume historical mean ~0, std ~1.5% daily
                flow_z = avg_change / 1.5

                # Cap at reasonable range
                flow_z = max(-3.0, min(3.0, flow_z))

                # Approximate USD flow (rough proxy)
                total_volume = stocks[volume_col].sum()
                flow_usd = total_volume * 0.001  # rough KES to USD proxy

                interpretation = (
                    f"Inflows (avg change: {avg_change:+.2f}%)" if flow_z > 0.5
                    else f"Outflows (avg change: {avg_change:+.2f}%)" if flow_z < -0.5
                    else f"Neutral (avg change: {avg_change:+.2f}%)"
                )

                logger.info(f"NSE flow signal: Z={flow_z:.2f}, {interpretation}")

                return {
                    'flow_z': round(flow_z, 3),
                    'flow_usd': round(flow_usd, 0),
                    'interpretation': interpretation,
                    'source': 'NSE_DERIVED',
                    'stocks_used': len(stocks),
                    'avg_price_change': round(avg_change, 4)
                }

            else:
                logger.warning(f"Expected columns not found. Available: {list(stocks.columns)}")
                return {
                    'flow_z': 0.0,
                    'flow_usd': 0.0,
                    'interpretation': 'Column mismatch — neutral assumption',
                    'source': 'NSE_COLUMN_MISMATCH',
                    'available_columns': list(stocks.columns)
                }

        except Exception as e:
            logger.error(f"Flow calculation error: {e}")
            return {
                'flow_z': 0.0,
                'flow_usd': 0.0,
                'interpretation': f'Calculation error: {e}',
                'source': 'NSE_ERROR'
            }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    nse = NSECollector()

    print("\n--- All Stocks ---")
    stocks = nse.get_all_stocks()
    print(f"Found {len(stocks)} stocks")
    if not stocks.empty:
        print(f"Columns: {list(stocks.columns)}")
        print(stocks.head(3))

    print("\n--- Capital Flow Signal ---")
    signal = nse.calculate_capital_flow_signal()
    for k, v in signal.items():
        print(f"  {k}: {v}")
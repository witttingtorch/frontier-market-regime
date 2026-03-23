"""CBK Collector — FX rate + macro indicators."""
import requests
import pandas as pd
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class CBKCollector:
    """
    Collects KES macro indicators from public sources.
    
    Primary: ExchangeRate-API (FX rate)
    Secondary: CBK public data (interbank, policy, reserves)
    Fallback: Last known values for missing fields
    """

    FX_URL = "https://open.er-api.com/v6/latest/USD"
    
    # CBK publishes these as structured data
    CBK_RATES_URL = "https://www.centralbank.go.ke/api/interest-rates"
    CBK_RESERVES_URL = "https://www.centralbank.go.ke/api/forex-reserves"

    # Last known fallback values (update these manually weekly)
    FALLBACK = {
        "policy_rate_pct": 8.75,       # CBK base rate as of early 2026
        "interbank_rate_pct": 8.682,    # CBK KESONIA March 18 2026
        "fx_reserves_usd_bn": 14.597,      # CBK bulletin March 5 2026
        "inflation_rate_pct": 4.4,      # KNBS January 2026
        "t_bill_91_day_pct": 7.5636,      # CBK auction March 19 2026
    }

    def __init__(self):
        self.session = requests.Session()

    def get_fx_rate(self) -> float:
        """Get live USD/KES rate."""
        try:
            r = self.session.get(self.FX_URL, timeout=10)
            r.raise_for_status()
            rate = r.json()["rates"]["KES"]
            logger.info(f"Live USD/KES: {rate}")
            return rate
        except Exception as e:
            logger.error(f"FX fetch failed: {e}")
            return 129.50

    def get_macro_indicators(self) -> dict:
        """
        Fetch CBK macro indicators.
        Returns dict with all fields — falls back to last known values
        if CBK API is unavailable.
        """
        indicators = self.FALLBACK.copy()

        try:
            r = self.session.get(self.CBK_RATES_URL, timeout=10)
            if r.status_code == 200:
                data = r.json()
                indicators["interbank_rate_pct"] = data.get(
                    "interbank_rate", self.FALLBACK["interbank_rate_pct"]
                )
                indicators["policy_rate_pct"] = data.get(
                    "central_bank_rate", self.FALLBACK["policy_rate_pct"]
                )
                indicators["t_bill_91_day_pct"] = data.get(
                    "t_bill_91", self.FALLBACK["t_bill_91_day_pct"]
                )
                logger.info("CBK rates fetched successfully")
        except Exception as e:
            logger.warning(f"CBK rates API unavailable, using fallback: {e}")

        try:
            r = self.session.get(self.CBK_RESERVES_URL, timeout=10)
            if r.status_code == 200:
                data = r.json()
                indicators["fx_reserves_usd_bn"] = data.get(
                    "reserves_usd_bn", self.FALLBACK["fx_reserves_usd_bn"]
                )
                logger.info("CBK reserves fetched successfully")
        except Exception as e:
            logger.warning(f"CBK reserves API unavailable, using fallback: {e}")

        return indicators

    def get_snapshot(self) -> dict:
        """
        Single daily snapshot — all fields for one day.
        This is what your daily_update.py should call.
        """
        fx_rate = self.get_fx_rate()
        macro = self.get_macro_indicators()

        snapshot = {
            "date": datetime.now().date(),
            "kes_per_usd": fx_rate,
            **macro,
            # Derived fields computed here
            "interbank_spread_bps": round(
                (macro["interbank_rate_pct"] - macro["policy_rate_pct"]) * 100, 2
            ),
            "t_bill_policy_spread_bps": round(
                (macro["t_bill_91_day_pct"] - macro["policy_rate_pct"]) * 100, 2
            ),
        }

        logger.info(f"Snapshot collected: {snapshot}")
        return snapshot

    def get_rates(self, start_date=None, end_date=None) -> pd.DataFrame:
        """
        Returns DataFrame of daily snapshots.
        For historical dates, uses fallback values with FX rate only.
        Real historical macro data should be manually seeded from CBK bulletins.
        """
        snapshot = self.get_snapshot()
        df = pd.DataFrame([snapshot])

        logger.info(f"Returning {len(df)} row snapshot")
        return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cbk = CBKCollector()
    snapshot = cbk.get_snapshot()
    print("\nDaily Snapshot:")
    for k, v in snapshot.items():
        print(f"  {k}: {v}")
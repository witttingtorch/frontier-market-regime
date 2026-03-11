"""Configuration for Frontier Market Regime Classification."""

import os
from dataclasses import dataclass
from typing import Dict


@dataclass
class MarketConfig:
    """Configuration for a specific market."""
    name: str
    currency_pair: str
    central_bank: str
    timezone: str
    fx_vol_threshold_green: float = 0.04   # 4%
    fx_vol_threshold_red: float = 0.08     # 8%
    inflation_threshold_green: float = 0.05  # 5%
    inflation_threshold_red: float = 0.08    # 8%
    reserve_threshold_green: float = 0.0     # Increasing
    reserve_threshold_red: float = -3        # 3 months decline


# Market configurations
MARKETS: Dict[str, MarketConfig] = {
    'nairobi': MarketConfig(
        name='Nairobi',
        currency_pair='KESUSD',
        central_bank='CBK',
        timezone='Africa/Nairobi',
        fx_vol_threshold_green=0.04,
        fx_vol_threshold_red=0.08
    ),
    'baku': MarketConfig(
        name='Baku',
        currency_pair='AZNUSD',
        central_bank='CBA',
        timezone='Asia/Baku',
        fx_vol_threshold_green=0.01,  # Lower for managed float
        fx_vol_threshold_red=0.03,
        inflation_threshold_red=0.12  # Said calibration — Baku absorbed 8-9% historically
    )
}

# Directory paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
RAW_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
LOGS_DIR = os.path.join(DATA_DIR, 'logs')

# API endpoints (no keys needed for CBK/CBA)
CBK_FX_URL = "https://www.centralbank.go.ke/wp-admin/admin-ajax.php"
CBA_SOAP_URL = "http://api.cba.am/exchangerates.asmx"

# Ensure directories exist
for d in [RAW_DIR, PROCESSED_DIR, LOGS_DIR]:
    os.makedirs(d, exist_ok=True)

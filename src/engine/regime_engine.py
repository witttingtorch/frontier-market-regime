"""Frontier Market Regime Classification Engine."""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Regime(Enum):
    """Market regime classifications."""
    RISK_ON = "Risk-On"
    DEFENSIVE = "Defensive"
    INSTABILITY = "Instability"


@dataclass
class VariableScore:
    """Score for individual variable."""
    name: str
    value: float
    score: int
    threshold_green: float
    threshold_red: float
    interpretation: str


class RegimeEngine:
    """Implements scoring algorithm from framework Section 2."""
    
    def __init__(self, market_config):
        self.config = market_config
    
    def calculate_fx_volatility(self, rates: pd.Series, window: int = 30) -> float:
        """Calculate annualized FX volatility."""
        if len(rates) < window:
            return np.nan
        log_returns = np.log(rates / rates.shift(1))
        volatility = log_returns.rolling(window=window).std() * np.sqrt(252)
        return volatility.iloc[-1]
    
    def score_fx_volatility(self, current_vol: float) -> VariableScore:
        """Score FX volatility: Green < 4%, Red > 8%."""
        if np.isnan(current_vol):
            return VariableScore("FX Volatility", current_vol, 0,
                self.config.fx_vol_threshold_green, self.config.fx_vol_threshold_red,
                "Insufficient data")
        
        if current_vol < self.config.fx_vol_threshold_green:
            score, interp = 1, f"Low volatility ({current_vol:.2%})"
        elif current_vol > self.config.fx_vol_threshold_red:
            score, interp = -1, f"High volatility ({current_vol:.2%})"
        else:
            score, interp = 0, f"Moderate volatility ({current_vol:.2%})"
        
        return VariableScore("FX Volatility", current_vol, score,
            self.config.fx_vol_threshold_green, self.config.fx_vol_threshold_red, interp)
    
    def score_policy_trajectory(self, current_rate: float,
                                previous_rate: float,
                                rate_3m_ago: float) -> VariableScore:
        """Score monetary policy: Green = stable/cutting, Red = hiking."""
        change_3m = current_rate - rate_3m_ago
        
        if change_3m <= 0:
            score, interp = 1, f"Accommodative ({change_3m:+.2f}bps)"
        elif change_3m > 100:
            score, interp = -1, f"Aggressive hiking (+{change_3m:.0f}bps)"
        else:
            score, interp = 0, f"Neutral ({change_3m:+.0f}bps)"
        
        return VariableScore("Policy Trajectory", current_rate, score, 0, 100, interp)
    
    def score_reserve_dynamics(self, current: float,
                               prev: float,
                               prev_3m: float) -> VariableScore:
        """Score reserve dynamics: Green = increasing, Red = 3mo decline."""
        monthly_change = current - prev
        change_3m = current - prev_3m
        consecutive_decline = monthly_change < 0 and (prev - prev_3m/3) < 0
        
        if monthly_change > 0:
            score, interp = 1, f"Increasing (+{monthly_change:.0f}M)"
        elif consecutive_decline:
            score, interp = -1, f"3-month decline ({change_3m:.0f}M)"
        else:
            score, interp = 0, f"Stable ({monthly_change:+.0f}M)"
        
        return VariableScore("Reserve Dynamics", current, score, 0, -3, interp)
    
    def score_inflation_momentum(self, cpi_current: float,
                                  cpi_prev: float,
                                  cpi_12m_ago: float) -> VariableScore:
        """Score inflation: Green < 5% and falling, Red > 8% and accelerating."""
        yoy = (cpi_current - cpi_12m_ago) / cpi_12m_ago
        mom = (cpi_current - cpi_prev) / cpi_prev
        accelerating = mom > 0
        
        if yoy < self.config.inflation_threshold_green and (not accelerating or yoy < 0.03):
            score, interp = 1, f"Low and stable ({yoy:.1%})"
        elif yoy > self.config.inflation_threshold_red and accelerating:
            score, interp = -1, f"High and accelerating ({yoy:.1%})"
        else:
            score, interp = 0, f"Moderate ({yoy:.1%})"
        
        return VariableScore("Inflation Momentum", yoy, score,
            self.config.inflation_threshold_green, self.config.inflation_threshold_red, interp)
    
    def score_capital_flows(self, flow_z: float, flow_usd: float) -> VariableScore:
        """Score capital flows: Green >= -0.5σ, Red < -2σ."""
        if flow_z >= -0.5:
            score, interp = 1, f"Normal (Z: {flow_z:+.2f})"
        elif flow_z < -2.0:
            score, interp = -1, f"Severe outflows (Z: {flow_z:+.2f})"
        else:
            score, interp = 0, f"Weak (Z: {flow_z:+.2f})"
        
        return VariableScore("Capital Flow Pressure", flow_z, score, -0.5, -2.0, interp)
    
    def compute_regime(self, variables: Dict[str, VariableScore],
                       override: Optional[Regime] = None) -> Tuple[Regime, str, int]:
        """Compute regime from variable scores. Human override takes precedence."""
        if override is not None:
            return override, "HUMAN_OVERRIDE", 0
        
        total_score = sum(v.score for v in variables.values())
        instability = any(v.score == -1 for v in variables.values())
        
        if instability:
            regime, source = Regime.INSTABILITY, "INSTABILITY_TRIGGER"
        elif total_score >= 3:
            regime, source = Regime.RISK_ON, "QUANTITATIVE"
        elif total_score >= 1:
            regime, source = Regime.DEFENSIVE, "QUANTITATIVE"
        else:
            regime, source = Regime.INSTABILITY, "QUANTITATIVE"
        
        return regime, source, total_score
    
    def generate_report(self, variables: Dict[str, VariableScore],
                        regime: Regime, source: str, total_score: int) -> str:
        """Generate human-readable report."""
        lines = [
            "=" * 60,
            f"REGIME CLASSIFICATION - {self.config.name}",
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
            "",
            "VARIABLE SCORES:",
            "-" * 40
        ]
        
        for v in variables.values():
            emoji = "🟢" if v.score == 1 else "🔴" if v.score == -1 else "🟡"
            lines.append(f"{emoji} {v.name:20} | {v.score:+d} | {v.interpretation}")
        
        lines.extend([
            "",
            "AGGREGATE:",
            "-" * 40,
            f"Total Score: {total_score:+d}",
            f"Regime: {regime.value}",
            f"Source: {source}",
            "=" * 60
        ])
        
        return "\n".join(lines)

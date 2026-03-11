"""Test regime engine."""

import sys
sys.path.insert(0, 'src')

from config import MARKETS
from engine import RegimeEngine, Regime

print("=" * 60)
print("TESTING REGIME ENGINE")
print("=" * 60)

nairobi_config = MARKETS['nairobi']
engine = RegimeEngine(nairobi_config)

variables = {
    'fx_vol': engine.score_fx_volatility(0.035),
    'policy': engine.score_policy_trajectory(13.0, 13.0, 13.5),
    'reserves': engine.score_reserve_dynamics(8500, 8400, 8300),
    'inflation': engine.score_inflation_momentum(105.2, 104.8, 100.0),
    'flows': engine.score_capital_flows(-0.3, -50)
}

regime, source, score = engine.compute_regime(variables)

print(f"\nMarket: {nairobi_config.name}")
print(f"Score: {score:+d}")
print(f"Regime: {regime.value}")
print(f"Source: {source}")
print("\n" + engine.generate_report(variables, regime, source, score))

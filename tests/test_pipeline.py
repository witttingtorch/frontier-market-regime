"""Test pipeline."""

import sys
sys.path.insert(0, 'src')
sys.path.insert(0, 'pipeline')

from pipeline.daily_update import DailyPipeline
from pipeline.alert_system import AlertSystem, AlertLevel

print("=" * 60)
print("TESTING PIPELINE")
print("=" * 60)

# Test pipeline (without full run)
pipeline = DailyPipeline()

# Test alert system
print("\n--- Alert System ---")
alerts = AlertSystem()
alerts.check_regime_change("nairobi", "Risk-On")
alerts.check_regime_change("nairobi", "Defensive")
print(alerts.summary())

print("\n✅ Pipeline components loaded successfully!")

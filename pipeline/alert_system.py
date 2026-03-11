"""Alert system for regime changes."""

import logging
from datetime import datetime
from typing import List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Alert:
    """Single alert."""
    
    def __init__(self, market: str, level: AlertLevel, 
                 message: str, regime_change: Optional[str] = None):
        self.market = market
        self.level = level
        self.message = message
        self.regime_change = regime_change
        self.timestamp = datetime.now()
    
    def __str__(self):
        return f"[{self.level.value.upper()}] {self.market}: {self.message}"


class AlertSystem:
    """Manage and send alerts."""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.last_regimes = {}  # Track last known regimes
    
    def check_regime_change(self, market: str, new_regime: str):
        """Check if regime changed and create alert."""
        old_regime = self.last_regimes.get(market)
        
        if old_regime and old_regime != new_regime:
            # Regime changed!
            if new_regime == "Instability":
                level = AlertLevel.CRITICAL
            elif new_regime == "Defensive" and old_regime == "Risk-On":
                level = AlertLevel.WARNING
            else:
                level = AlertLevel.INFO
            
            alert = Alert(
                market=market,
                level=level,
                message=f"Regime changed: {old_regime} → {new_regime}",
                regime_change=f"{old_regime}→{new_regime}"
            )
            self.alerts.append(alert)
            self._send_alert(alert)
        
        self.last_regimes[market] = new_regime
    
    def _send_alert(self, alert: Alert):
        """Send alert via available channels."""
        # Log alert
        log_func = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.CRITICAL: logger.error
        }.get(alert.level, logger.info)
        
        log_func(str(alert))
        
        # TODO: Add email, Slack, SMS notifications here
        # Examples:
        # - Send email via smtplib
        # - Post to Slack webhook
        # - Send SMS via Twilio
    
    def add_manual_alert(self, market: str, message: str, 
                         level: AlertLevel = AlertLevel.INFO):
        """Add manual alert (e.g., from override)."""
        alert = Alert(market, level, message)
        self.alerts.append(alert)
        self._send_alert(alert)
    
    def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """Get alerts from last N hours."""
        cutoff = datetime.now() - __import__('datetime').timedelta(hours=hours)
        return [a for a in self.alerts if a.timestamp > cutoff]
    
    def summary(self) -> str:
        """Get alert summary."""
        if not self.alerts:
            return "No alerts"
        
        lines = ["ALERT SUMMARY:", "=" * 40]
        for alert in self.alerts[-10:]:  # Last 10
            lines.append(f"{alert.timestamp.strftime('%H:%M')} {alert}")
        
        return "\n".join(lines)


def send_alert(market: str, message: str, level: str = "warning"):
    """Quick alert function."""
    alert_sys = AlertSystem()
    alert_sys.add_manual_alert(
        market, 
        message, 
        AlertLevel[level.lower()]
    )


if __name__ == "__main__":
    # Test alerts
    alerts = AlertSystem()
    alerts.check_regime_change("nairobi", "Risk-On")
    alerts.check_regime_change("nairobi", "Defensive")
    alerts.check_regime_change("nairobi", "Instability")
    print(alerts.summary())

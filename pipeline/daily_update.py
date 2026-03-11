"""Daily data collection and regime classification."""

import sys
sys.path.insert(0, 'src')

import pandas as pd
from datetime import datetime
from typing import Dict, Optional
import logging

from config import MARKETS
from collectors.cbk_collector import CBKCollector
from collectors.cba_collector import CBACollector
from engine.regime_engine import RegimeEngine, Regime
from utils.logging_config import setup_logging
from utils.data_quality import validate_data

logger = setup_logging()


class DailyPipeline:
    """Automated daily data collection and classification."""

    def __init__(self):
        self.collectors = {
            'nairobi': CBKCollector(),
            'baku': CBACollector(),
        }
        self.engines = {
            'nairobi': RegimeEngine(MARKETS['nairobi']),
            'baku': RegimeEngine(MARKETS['baku'])
        }
        self.results = {}

    def collect_fx_data(self, market: str, days: int = 30) -> pd.DataFrame:
        """Collect FX rates for market."""
        logger.info(f"Collecting FX data for {market}")

        try:
            if market == 'nairobi':
                df = self.collectors[market].get_rates(currency='USD')
            else:
                df = self.collectors[market].get_usd_history(days=days)
        except Exception as e:
            logger.error(f"Collection failed for {market}: {e}")
            return pd.DataFrame()

        validation = validate_data(
            df,
            ['date', 'rate'] if market == 'nairobi' else ['currency', 'azn_per_unit']
        )
        if not validation['valid']:
            logger.warning(f"Data quality issues: {validation['issues']}")

        return df

    def calculate_regime(self, market: str,
                         fx_data: pd.DataFrame,
                         manual_inputs: Optional[Dict] = None) -> Dict:
        """Calculate regime classification."""
        logger.info(f"Calculating regime for {market}")

        engine = self.engines[market]

        # Determine rate column
        rate_col = 'kes_per_usd' if market == 'nairobi' else 'azn_per_unit'
        if rate_col not in fx_data.columns:
            rate_col = 'rate' if 'rate' in fx_data.columns else fx_data.columns[-1]

        fx_vol = engine.calculate_fx_volatility(fx_data[rate_col])

        manual_inputs = manual_inputs or {}

        variables = {
            'fx_vol': engine.score_fx_volatility(fx_vol),
            'policy': engine.score_policy_trajectory(
                manual_inputs.get('policy_rate', 13.0),
                manual_inputs.get('policy_prev', 13.0),
                manual_inputs.get('policy_3m', 13.5)
            ),
            'reserves': engine.score_reserve_dynamics(
                manual_inputs.get('reserves', 8000),
                manual_inputs.get('reserves_prev', 7900),
                manual_inputs.get('reserves_3m', 7800)
            ),
            'inflation': engine.score_inflation_momentum(
                manual_inputs.get('cpi', 105.0),
                manual_inputs.get('cpi_prev', 104.5),
                manual_inputs.get('cpi_12m', 100.0)
            ),
            'flows': engine.score_capital_flows(
                manual_inputs.get('flow_z', 0.0),
                manual_inputs.get('flow_usd', 0)
            )
        }

        override = manual_inputs.get('override')
        if override:
            override = Regime[override]

        regime, source, score = engine.compute_regime(variables, override)

        result = {
            'market': market,
            'date': datetime.now(),
            'regime': regime.value,
            'source': source,
            'score': score,
            'variables': {k: v.score for k, v in variables.items()},
            'fx_volatility': fx_vol,
            'report': engine.generate_report(variables, regime, source, score)
        }

        self.results[market] = result
        return result

    def save_results(self):
        """Save classification results to CSV and log files."""
        if not self.results:
            logger.warning("No results to save")
            return

        for market, result in self.results.items():
            filename = f"data/processed/{market}_regime_{datetime.now().strftime('%Y%m%d')}.csv"

            record = {
                'date': result['date'],
                'market': result['market'],
                'regime': result['regime'],
                'score': result['score'],
                'source': result['source'],
                'fx_volatility': result['fx_volatility'],
                **result['variables']
            }

            pd.DataFrame([record]).to_csv(filename, index=False)
            logger.info(f"Saved: {filename}")

            report_file = f"data/logs/{market}_report_{datetime.now().strftime('%Y%m%d')}.txt"
            with open(report_file, 'w') as f:
                f.write(result['report'])
            logger.info(f"Saved report: {report_file}")

    def run(self, markets: list = None):
        """Run full pipeline for specified markets."""
        markets = markets or ['nairobi']

        logger.info("=" * 60)
        logger.info("STARTING DAILY PIPELINE")
        logger.info("=" * 60)

        for market in markets:
            try:
                logger.info(f"\nProcessing {market}...")

                fx_data = self.collect_fx_data(market)

                if fx_data.empty:
                    logger.error(f"No FX data for {market} — skipping")
                    continue

                result = self.calculate_regime(market, fx_data)
                logger.info(f"Regime: {result['regime']} (Score: {result['score']:+d})")

            except Exception as e:
                logger.error(f"Error processing {market}: {e}")

        self.save_results()

        logger.info("\n" + "=" * 60)
        logger.info("PIPELINE COMPLETE")
        logger.info("=" * 60)


if __name__ == "__main__":
    # Default: nairobi only
    # Override: python pipeline/daily_update.py --markets nairobi,baku
    markets = None
    if '--markets' in sys.argv:
        idx = sys.argv.index('--markets')
        markets = sys.argv[idx + 1].split(',')

    pipeline = DailyPipeline()
    pipeline.run(markets=markets)
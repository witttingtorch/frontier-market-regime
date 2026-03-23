"""
Streamlit app for manual regime classification.
Run with: streamlit run app/manual_entry.py
"""

import sys
sys.path.insert(0, 'src')

import streamlit as st
import pandas as pd
from datetime import datetime
import os

from config import MARKETS
from engine import RegimeEngine, Regime
from collectors.cbk_collector import CBKCollector
from collectors.cba_collector import CBACollector

st.set_page_config(
    page_title="Frontier Market Regime Classifier",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .regime-risk-on {
        background-color: #1a4731; color: #2ecc71;
        padding: 1rem; border-radius: 0.5rem;
        font-size: 1.8rem; font-weight: bold;
        text-align: center; margin-bottom: 1rem;
    }
    .regime-defensive {
        background-color: #4a3800; color: #f39c12;
        padding: 1rem; border-radius: 0.5rem;
        font-size: 1.8rem; font-weight: bold;
        text-align: center; margin-bottom: 1rem;
    }
    .regime-instability {
        background-color: #4a1020; color: #e74c3c;
        padding: 1rem; border-radius: 0.5rem;
        font-size: 1.8rem; font-weight: bold;
        text-align: center; margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def get_fx_data(market: str):
    try:
        if market == 'nairobi':
            collector = CBKCollector()
            df = collector.get_rates()
            return df, 'kes_per_usd' if 'kes_per_usd' in df.columns else 'rate'
        else:
            collector = CBACollector()
            df = collector.get_usd_history(days=30)
            return df, 'azn_per_unit'
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame(), 'rate'


def load_log(market_key: str) -> pd.DataFrame:
    filepath = f"data/processed/{market_key}_regime_log.csv"
    try:
        return pd.read_csv(filepath)
    except FileNotFoundError:
        return pd.DataFrame()


def save_to_csv(record: dict, market_key: str) -> pd.DataFrame:
    os.makedirs('data/processed', exist_ok=True)
    filepath = f"data/processed/{market_key}_regime_log.csv"
    try:
        existing = pd.read_csv(filepath)
        updated = pd.concat([existing, pd.DataFrame([record])], ignore_index=True)
    except FileNotFoundError:
        updated = pd.DataFrame([record])
    updated.to_csv(filepath, index=False)
    return updated


for key, val in [
    ('fx_rate_value', 129.16),
    ('fetched_rate_display', None),
    ('inputs', {}),
    ('result', None)
]:
    if key not in st.session_state:
        st.session_state[key] = val

st.title("🌍 Frontier Market Regime Classification")
st.markdown("*Hybrid Human-Quantitative Architecture for Non-Stationary Environments*")
st.markdown("---")

st.sidebar.header("Settings")
market = st.sidebar.selectbox("Select Market", ["Nairobi (KES)", "Baku (AZN)"], index=0)
market_key = 'nairobi' if 'Nairobi' in market else 'baku'
config = MARKETS[market_key]

st.sidebar.markdown(f"**Central Bank:** {config.central_bank}")
st.sidebar.markdown(f"**Currency:** {config.currency_pair}")
st.sidebar.markdown("---")
st.sidebar.subheader("Auto-Fetch Data")

if st.sidebar.button("🔄 Fetch Latest FX Rates"):
    with st.spinner("Fetching..."):
        fx_df, rate_col = get_fx_data(market_key)
        if not fx_df.empty:
            latest_rate = float(fx_df[rate_col].iloc[-1])
            latest_date = fx_df['date'].iloc[-1] if 'date' in fx_df.columns else datetime.now()
            st.session_state['fx_rate_value'] = latest_rate
            st.session_state['fetched_rate_display'] = f"Rate: {latest_rate:.4f} | Date: {latest_date}"
            st.rerun()
        else:
            st.sidebar.error("No data fetched")

if st.session_state['fetched_rate_display']:
    st.sidebar.success(st.session_state['fetched_rate_display'])

tab1, tab2, tab3 = st.tabs(["📊 Data Entry", "📈 Analysis", "📝 Logs"])

with tab1:
    st.header("Market Data Entry")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("1. FX & Monetary")

        fx_rate = st.number_input(
            f"{config.currency_pair} Rate",
            value=float(st.session_state['fx_rate_value']),
            step=0.01, format="%.4f"
        )
        st.session_state['fx_rate_value'] = fx_rate

        fx_vol = st.number_input(
            "FX Volatility (%)",
            value=4.0, step=0.1, min_value=0.0, max_value=50.0,
            key='fx_vol_input'
        ) / 100

        policy_rate = st.number_input(
            "Central Bank Rate (%)",
            value=8.75 if market_key == 'nairobi' else 7.0,
            step=0.25, key='policy_rate_input'
        )

        interbank_rate = st.number_input(
            "Interbank Rate (%)",
            value=8.682 if market_key == 'nairobi' else 7.15,
            step=0.05, key='interbank_rate_input',
            help="Daily interbank lending rate. Spread vs policy rate = liquidity signal."
        )

        interbank_spread_bps = round((interbank_rate - policy_rate) * 100, 2)
        spread_color = "🟢" if interbank_spread_bps < 50 else "🟡" if interbank_spread_bps < 150 else "🔴"
        st.markdown(f"**Interbank Spread:** {spread_color} `{interbank_spread_bps} bps`")

        policy_direction = st.selectbox(
            "Policy Direction",
            ["Cutting", "Stable", "Hiking"],
            key='policy_dir_input'
        )

    with col2:
        st.subheader("2. Reserves & Inflation")

        reserves = st.number_input(
            "FX Reserves (USD Millions)",
            value=14597.0, step=100.0, key='reserves_input'
        )
        reserves_change = st.number_input(
            "Monthly Change (USD Millions)",
            value=120.0, step=10.0, key='reserves_chg_input'
        )
        cpi_yoy = st.number_input(
            "CPI YoY Inflation (%)",
            value=4.4, step=0.1, key='cpi_yoy_input'
        ) / 100
        cpi_mom = st.number_input(
            "CPI MoM Change (%)",
            value=0.3, step=0.1, key='cpi_mom_input'
        ) / 100

        tbill_91 = st.number_input(
            "91-Day T-Bill Yield (%)",
            value=7.5636, step=0.05, key='tbill_input',
            help="Weekly CBK auction result. Rising yield = liquidity tightening."
        )

    with col3:
        st.subheader("3. Capital Flows")

        flow_z = st.number_input(
            "Capital Flow Z-Score",
            value=-0.3, step=0.1, key='flow_z_input'
        )
        flow_usd = st.number_input(
            "Net Flow (USD Millions)",
            value=-50.0, step=10.0, key='flow_usd_input'
        )

        st.markdown("---")
        st.subheader("4. Human Override")

        override = st.selectbox(
            "Override Regime (Optional)",
            ["None", "Risk-On", "Defensive", "Instability"],
            index=0, key='override_input'
        )
        override_reason = st.text_area(
            "Override Reasoning",
            placeholder="Why are you overriding the model?",
            key='override_reason_input'
        )

    st.markdown("---")
    col_left, col_mid, col_right = st.columns([1, 2, 1])

    with col_mid:
        if st.button("🔍 CALCULATE REGIME", type="primary", use_container_width=True):
            with st.spinner("Calculating..."):
                engine = RegimeEngine(config)

                variables = {
                    'fx_vol': engine.score_fx_volatility(fx_vol),
                    'policy': engine.score_policy_trajectory(
                        policy_rate,
                        policy_rate - (0.25 if policy_direction == "Hiking" else -0.25),
                        policy_rate - (0.5 if policy_direction == "Hiking" else -0.5)
                    ),
                    'reserves': engine.score_reserve_dynamics(
                        reserves,
                        reserves - reserves_change,
                        reserves - reserves_change * 3
                    ),
                    'inflation': engine.score_inflation_momentum(
                        100 * (1 + cpi_yoy),
                        100 * (1 + cpi_yoy - cpi_mom),
                        100
                    ),
                    'flows': engine.score_capital_flows(flow_z, flow_usd)
                }

                regime_override = None
                if override != "None":
                    regime_override = Regime[override.upper().replace("-", "_")]

                regime, source, score = engine.compute_regime(variables, regime_override)

                st.session_state['result'] = {
                    'regime': regime,
                    'source': source,
                    'score': score,
                    'variables': variables,
                    'report': engine.generate_report(variables, regime, source, score)
                }

                st.session_state['inputs'] = {
                    'fx_rate': fx_rate,
                    'fx_vol': fx_vol,
                    'policy_rate': policy_rate,
                    'interbank_rate': interbank_rate,
                    'interbank_spread_bps': interbank_spread_bps,
                    'policy_direction': policy_direction,
                    'reserves': reserves,
                    'reserves_change': reserves_change,
                    'cpi_yoy': cpi_yoy,
                    'cpi_mom': cpi_mom,
                    'tbill_91': tbill_91,
                    'flow_z': flow_z,
                    'flow_usd': flow_usd,
                    'override': override,
                    'override_reason': override_reason
                }

                st.success("Calculation complete! Go to Analysis tab to view and save.")

with tab2:
    st.header("Regime Analysis")

    if st.session_state['result']:
        result = st.session_state['result']
        inputs = st.session_state.get('inputs', {})

        regime_class = {
            Regime.RISK_ON:     "regime-risk-on",
            Regime.DEFENSIVE:   "regime-defensive",
            Regime.INSTABILITY: "regime-instability"
        }.get(result['regime'], "regime-defensive")

        regime_emoji = {
            Regime.RISK_ON:     "🟢",
            Regime.DEFENSIVE:   "🟡",
            Regime.INSTABILITY: "🔴"
        }.get(result['regime'], "⚪")

        st.markdown(
            f'<div class="{regime_class}">{regime_emoji} {result["regime"].value}</div>',
            unsafe_allow_html=True
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Aggregate Score", f"{result['score']:+d}")
        col2.metric("Source", result['source'])
        col3.metric(
            "Confidence",
            "High" if abs(result['score']) >= 4
            else "Medium" if abs(result['score']) >= 2
            else "Low"
        )
        col4.metric("Interbank Spread", f"{inputs.get('interbank_spread_bps', 0)} bps")

        if inputs.get('override_reason'):
            st.info(f"**Override Reasoning:** {inputs['override_reason']}")

        st.subheader("Variable Breakdown")

        var_data = []
        for name, var in result['variables'].items():
            var_data.append({
                'Variable': var.name,
                'Score': var.score,
                'Value': f"{var.value:.2%}" if "vol" in name.lower() or "inflation" in name.lower()
                         else f"{var.value:.2f}",
                'Interpretation': var.interpretation
            })

        df_vars = pd.DataFrame(var_data)

        def color_score(val):
            if val == 1:  return 'background-color: #1a4731; color: #2ecc71'
            if val == -1: return 'background-color: #4a1020; color: #e74c3c'
            return 'background-color: #4a3800; color: #f39c12'

        st.dataframe(
            df_vars.style.map(color_score, subset=['Score']),
            use_container_width=True
        )

        st.subheader("Liquidity Indicators")
        liq1, liq2, liq3 = st.columns(3)
        spread = inputs.get('interbank_spread_bps', 0)
        liq1.metric("Interbank Spread", f"{spread} bps",
                    delta="⚠️ Elevated" if spread > 100 else "✅ Normal")
        tbill_spread = round((inputs.get('tbill_91', 0) - inputs.get('policy_rate', 0)) * 100, 1)
        liq2.metric("T-Bill/Policy Spread", f"{tbill_spread} bps")
        liq3.metric("Reserves Change", f"{inputs.get('reserves_change', 0):+.0f} USD M")

        with st.expander("View Full Report"):
            st.text(result['report'])

        col_dl, col_save = st.columns(2)

        with col_dl:
            st.download_button(
                "📥 Download Report",
                result['report'],
                file_name=f"{market_key}_regime_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                use_container_width=True
            )

        with col_save:
            if st.button("💾 Save to CSV", use_container_width=True):
                record = {
                    'timestamp': datetime.now().isoformat(),
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'market': market_key,
                    'regime': result['regime'].value,
                    'score': result['score'],
                    'source': result['source'],
                    'fx_rate': inputs.get('fx_rate', 0),
                    'fx_volatility_pct': round(inputs.get('fx_vol', 0) * 100, 4),
                    'policy_rate': inputs.get('policy_rate', 0),
                    'interbank_rate': inputs.get('interbank_rate', 0),
                    'interbank_spread_bps': inputs.get('interbank_spread_bps', 0),
                    'policy_direction': inputs.get('policy_direction', ''),
                    'reserves_usd_m': inputs.get('reserves', 0),
                    'reserves_change_usd_m': inputs.get('reserves_change', 0),
                    'cpi_yoy_pct': round(inputs.get('cpi_yoy', 0) * 100, 4),
                    'cpi_mom_pct': round(inputs.get('cpi_mom', 0) * 100, 4),
                    'tbill_91_pct': inputs.get('tbill_91', 0),
                    'flow_z_score': inputs.get('flow_z', 0),
                    'flow_usd_m': inputs.get('flow_usd', 0),
                    'override': inputs.get('override', 'None'),
                    'override_reason': inputs.get('override_reason', ''),
                    'score_fx_vol': result['variables']['fx_vol'].score,
                    'score_policy': result['variables']['policy'].score,
                    'score_reserves': result['variables']['reserves'].score,
                    'score_inflation': result['variables']['inflation'].score,
                    'score_flows': result['variables']['flows'].score,
                }

                updated = save_to_csv(record, market_key)
                st.success(f"✅ Saved — {len(updated)} total records")

                with st.expander("View Saved Data"):
                    st.dataframe(updated.tail())
    else:
        st.info("Run calculation in Data Entry tab first.")

with tab3:
    st.header("Classification Logs")
    df_log = load_log(market_key)

    if not df_log.empty:
        st.success(f"{len(df_log)} records logged for {market}")

        col1, col2, col3 = st.columns(3)
        regime_counts = df_log['regime'].value_counts()
        col1.metric("Risk-On",     regime_counts.get('Risk-On', 0))
        col2.metric("Defensive",   regime_counts.get('Defensive', 0))
        col3.metric("Instability", regime_counts.get('Instability', 0))

        if 'interbank_spread_bps' in df_log.columns:
            st.subheader("Interbank Spread Trend")
            df_log['date'] = pd.to_datetime(df_log['date'])
            st.line_chart(df_log.sort_values('date').set_index('date')['interbank_spread_bps'])

        st.markdown("---")
        st.subheader("Recent Classifications")
        display_cols = ['date', 'regime', 'score', 'source']
        extra = ['fx_rate', 'fx_volatility_pct', 'interbank_spread_bps',
                 'policy_direction', 'cpi_yoy_pct', 'override']
        display_cols += [c for c in extra if c in df_log.columns]

        st.dataframe(
            df_log[display_cols].sort_values('date', ascending=False).head(20),
            use_container_width=True
        )

        st.download_button(
            "📥 Download Full Log",
            df_log.to_csv(index=False),
            file_name=f"{market_key}_regime_log_{datetime.now().strftime('%Y%m%d')}.csv"
        )
    else:
        st.info("No classifications saved yet. Use Data Entry tab to log your first entry.")

    st.markdown("---")
    with st.expander("📍 Add Street-Level Observation"):
        observation = st.text_area(
            "Street-level intelligence",
            placeholder="FX liquidity drying up, import delays, fuel shortages, USD hoarding..."
        )

        KEYWORDS = {
            'hoarding': -1, 'shortage': -1, 'delays': -1,
            'liquidity': -1, 'queues': -1, 'scarcity': -1,
            'stable': 1, 'improving': 1, 'abundant': 1,
            'normal': 1, 'flowing': 1
        }

        sentiment = 0
        matched = []
        if observation:
            obs_lower = observation.lower()
            matched = [k for k in KEYWORDS if k in obs_lower]
            sentiment = sum(KEYWORDS[k] for k in matched)
            if matched:
                st.markdown(f"**Detected signals:** `{', '.join(matched)}` → sentiment score: `{sentiment:+d}`")

        obs_confidence = st.selectbox("Confidence", ["Low", "Medium", "High"], key='obs_confidence')

        if st.button("Log Observation", type="secondary"):
            if observation:
                obs_record = {
                    'timestamp': datetime.now().isoformat(),
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'market': market_key,
                    'type': 'street_intelligence',
                    'observation': observation,
                    'confidence': obs_confidence,
                    'sentiment_score': sentiment,
                    'signals_detected': ', '.join(matched)
                }
                os.makedirs('data/processed', exist_ok=True)
                obs_file = f"data/processed/{market_key}_observations.csv"
                try:
                    existing = pd.read_csv(obs_file)
                    updated = pd.concat([existing, pd.DataFrame([obs_record])], ignore_index=True)
                except FileNotFoundError:
                    updated = pd.DataFrame([obs_record])
                updated.to_csv(obs_file, index=False)
                st.success(f"✅ Observation logged — sentiment: {sentiment:+d} — {len(updated)} total")
            else:
                st.warning("Enter an observation before logging.")

if __name__ == "__main__":
    pass

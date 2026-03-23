"""
Historical regime analysis dashboard.
Run with: streamlit run app/dashboard.py
"""

import sys
sys.path.insert(0, 'src')

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime
import os

st.set_page_config(
    page_title="Dual-Frontier Regime Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dual-Frontier Regime Dashboard")
st.markdown("*Nairobi (KES) vs Baku (AZN) — Historical Regime Analysis*")
st.markdown("---")

REGIME_COLORS = {
    'Risk-On':     '#2ecc71',
    'Defensive':   '#f39c12',
    'Instability': '#e74c3c'
}

REGIME_INT = {
    'Risk-On': 1,
    'Defensive': 0,
    'Instability': -1
}


def load_market(market_key: str) -> pd.DataFrame:
    path = f"data/processed/{market_key}_regime_log.csv"
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').drop_duplicates(subset='date', keep='last')
    df['regime_int'] = df['regime'].map(REGIME_INT)
    return df


def load_observations(market_key: str) -> pd.DataFrame:
    path = f"data/processed/{market_key}_observations.csv"
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date'])
    return df


# ── Load data ─────────────────────────────────────────────────────────────────

df_nairobi = load_market('nairobi')
df_baku    = load_market('baku')
obs_nairobi = load_observations('nairobi')
obs_baku    = load_observations('baku')

has_nairobi = not df_nairobi.empty
has_baku    = not df_baku.empty

if not has_nairobi and not has_baku:
    st.warning("No data yet. Use the Regime Classifier to log entries first.")
    st.stop()


# ── Summary metrics ───────────────────────────────────────────────────────────

st.subheader("Node Summary")
col1, col2, col3, col4 = st.columns(4)

if has_nairobi:
    latest_n = df_nairobi.iloc[-1]
    col1.metric(
        "🇰🇪 Nairobi Regime",
        latest_n['regime'],
        delta=f"Score: {latest_n['score']:+d}"
    )
    col2.metric("Nairobi Records", len(df_nairobi))

if has_baku:
    latest_b = df_baku.iloc[-1]
    col3.metric(
        "🇦🇿 Baku Regime",
        latest_b['regime'],
        delta=f"Score: {latest_b['score']:+d}"
    )
    col4.metric("Baku Records", len(df_baku))

st.markdown("---")


# ── Regime timeline ───────────────────────────────────────────────────────────

st.subheader("Regime Timeline")

fig, axes = plt.subplots(
    2 if (has_nairobi and has_baku) else 1,
    1,
    figsize=(14, 6),
    facecolor='#0e1117'
)

if has_nairobi and has_baku:
    ax_n, ax_b = axes
else:
    ax_n = axes if has_nairobi else None
    ax_b = axes if has_baku else None

def plot_regime_timeline(ax, df, title):
    ax.set_facecolor('#0e1117')
    for _, row in df.iterrows():
        color = REGIME_COLORS.get(row['regime'], '#888888')
        ax.bar(row['date'], 1, color=color, width=1, alpha=0.85)
    ax.set_title(title, color='white', fontsize=12, pad=8)
    ax.set_yticks([])
    ax.tick_params(colors='white')
    ax.spines['bottom'].set_color('#444')
    for spine in ['top', 'left', 'right']:
        ax.spines[spine].set_visible(False)

if has_nairobi and ax_n:
    plot_regime_timeline(ax_n, df_nairobi, "🇰🇪 Nairobi (KES)")

if has_baku and ax_b:
    plot_regime_timeline(ax_b, df_baku, "🇦🇿 Baku (AZN)")

legend_patches = [
    mpatches.Patch(color=c, label=r)
    for r, c in REGIME_COLORS.items()
]
fig.legend(
    handles=legend_patches,
    loc='lower center',
    ncol=3,
    facecolor='#0e1117',
    labelcolor='white',
    framealpha=0.3
)

plt.tight_layout(rect=[0, 0.05, 1, 1])
st.pyplot(fig)


# ── Synchronization analysis ──────────────────────────────────────────────────

if has_nairobi and has_baku:
    st.markdown("---")
    st.subheader("Node Synchronization")

    merged = pd.merge(
        df_nairobi[['date', 'regime', 'regime_int', 'score']].rename(
            columns={'regime': 'regime_nairobi', 'regime_int': 'int_nairobi', 'score': 'score_nairobi'}
        ),
        df_baku[['date', 'regime', 'regime_int', 'score']].rename(
            columns={'regime': 'regime_baku', 'regime_int': 'int_baku', 'score': 'score_baku'}
        ),
        on='date', how='inner'
    )

    if not merged.empty:
        sync_rate = (merged['regime_nairobi'] == merged['regime_baku']).mean()
        correlation = merged['int_nairobi'].corr(merged['int_baku'])

        s1, s2, s3 = st.columns(3)
        s1.metric("Regime Sync Rate", f"{sync_rate:.1%}",
                  help="% of days both nodes are in same regime")
        s2.metric("Regime Correlation", f"{correlation:.3f}",
                  help="Pearson correlation of regime scores. >0.5 = coupled, <0 = decoupled")
        s3.metric("Overlapping Days", len(merged))

        st.subheader("Day-by-Day Comparison")

        def style_regime(val):
            color = {'Risk-On': '#1a4731', 'Defensive': '#4a3800', 'Instability': '#4a1020'}.get(val, '')
            text = {'Risk-On': '#2ecc71', 'Defensive': '#f39c12', 'Instability': '#e74c3c'}.get(val, 'white')
            return f'background-color: {color}; color: {text}' if color else ''

        display = merged[['date', 'regime_nairobi', 'score_nairobi', 'regime_baku', 'score_baku']].copy()
        display['aligned'] = display['regime_nairobi'] == display['regime_baku']
        display = display.sort_values('date', ascending=False)

        st.dataframe(
            display.style
                .map(style_regime, subset=['regime_nairobi', 'regime_baku'])
                .map(lambda v: 'color: #2ecc71' if v else 'color: #e74c3c', subset=['aligned']),
            use_container_width=True
        )

        st.download_button(
            "📥 Download Sync Analysis",
            merged.to_csv(index=False),
            file_name=f"dual_frontier_sync_{datetime.now().strftime('%Y%m%d')}.csv"
        )
    else:
        st.info("No overlapping dates between nodes yet.")


# ── Interbank spread trend ────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Liquidity Indicators")

liq_col1, liq_col2 = st.columns(2)

if has_nairobi and 'interbank_spread_bps' in df_nairobi.columns:
    with liq_col1:
        st.markdown("**🇰🇪 Nairobi — Interbank Spread (bps)**")
        chart_data = df_nairobi.set_index('date')['interbank_spread_bps'].dropna()
        if not chart_data.empty:
            st.line_chart(chart_data)

if has_baku and 'interbank_spread_bps' in df_baku.columns:
    with liq_col2:
        st.markdown("**🇦🇿 Baku — Interbank Spread (bps)**")
        chart_data = df_baku.set_index('date')['interbank_spread_bps'].dropna()
        if not chart_data.empty:
            st.line_chart(chart_data)


# ── Street intelligence ───────────────────────────────────────────────────────

if not obs_nairobi.empty or not obs_baku.empty:
    st.markdown("---")
    st.subheader("📍 Street Intelligence Log")

    obs_tab1, obs_tab2 = st.tabs(["🇰🇪 Nairobi", "🇦🇿 Baku"])

    with obs_tab1:
        if not obs_nairobi.empty:
            st.dataframe(
                obs_nairobi[['date', 'observation', 'confidence', 'sentiment_score']]
                    .sort_values('date', ascending=False)
                    .head(10),
                use_container_width=True
            )
        else:
            st.info("No street observations logged for Nairobi yet.")

    with obs_tab2:
        if not obs_baku.empty:
            st.dataframe(
                obs_baku[['date', 'observation', 'confidence', 'sentiment_score']]
                    .sort_values('date', ascending=False)
                    .head(10),
                use_container_width=True
            )
        else:
            st.info("No street observations logged for Baku yet.")


st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Data: data/processed/")

if __name__ == "__main__":
    pass

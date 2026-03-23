"""
Advanced dashboard for historical analysis.
Run with: streamlit run app/dashboard.py
"""

import sys
sys.path.insert(0, 'src')

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="Regime Dashboard", layout="wide")

st.title("📊 Historical Regime Analysis")

# Placeholder for historical data
st.info("Connect to data/processed/ folder to display historical regime classifications")

# Example visualization
fig, ax = plt.subplots(figsize=(12, 6))

# Sample data (replace with actual historical data)
dates = pd.date_range(start='2024-01-01', periods=100, freq='B')
regimes = ['Risk-On'] * 40 + ['Defensive'] * 30 + ['Instability'] * 20 + ['Defensive'] * 10

colors = {'Risk-On': 'green', 'Defensive': 'orange', 'Instability': 'red'}
regime_colors = [colors[r] for r in regimes]

ax.scatter(dates, range(len(dates)), c=regime_colors, alpha=0.6, s=10)
ax.set_xlabel('Date')
ax.set_ylabel('Trading Days')
ax.set_title('Regime History (Sample)')

# Legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=c, label=r) for r, c in colors.items()]
ax.legend(handles=legend_elements)

st.pyplot(fig)

st.markdown("---")
st.caption("Load actual data from data/processed/*_regime_*.csv files")

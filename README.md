# Frontier Market Regime Classification Framework

> Hybrid Human-Quantitative architecture for regime detection in non-stationary frontier markets.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red.svg)](https://streamlit.io)
[![Status](https://img.shields.io/badge/Status-Active%20Research-green.svg)]()
[![Nodes](https://img.shields.io/badge/Nodes-Nairobi%20%7C%20Baku-orange.svg)]()

---

## Overview

Standard quantitative regime models assume liquid, informationally efficient markets. Frontier markets violate both assumptions. Price discovery is delayed, data is sparse, and regime transitions often manifest in street-level signals before appearing in statistics.

This framework addresses the **detection latency problem** through a hybrid architecture that combines a quantitative scoring engine with structured human override and street-level intelligence logging.

> *"Detection latency is social before it is statistical."*

---

## Live Nodes

| Market | Currency | Central Bank | Status | Analyst |
|--------|----------|-------------|--------|---------|
| Nairobi | KES | CBK | 🟢 Active — logging daily | Moses Martin |
| Baku | AZN | CBA | 🟢 Active — logging weekly | Said Taghizade, KPMG |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              QUANTITATIVE LAYER                      │
│                                                      │
│   FX Volatility  →  Score: +1 / 0 / -1              │
│   Policy Trajectory  →  Score: +1 / 0 / -1          │
│   Reserve Dynamics  →  Score: +1 / 0 / -1           │
│   Inflation Momentum  →  Score: +1 / 0 / -1         │
│   Capital Flow Pressure  →  Score: +1 / 0 / -1      │
│                                                      │
│   Aggregate Score: -5 to +5                         │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│              HUMAN LAYER                             │
│                                                      │
│   Analyst override with documented reasoning         │
│   Street-level intelligence logging                  │
│   Geopolitical signal flagging                       │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│              REGIME OUTPUT                           │
│                                                      │
│   🟢 Risk-On     Score >= +4                        │
│   🟡 Defensive   Score +1 to +3                     │
│   🔴 Instability Score <= 0                         │
└─────────────────────────────────────────────────────┘
```

---

## Market-Specific Threshold Calibration

A core theoretical contribution of this framework is that optimal thresholds are determined by central bank strategy type, not universal constants.

| Node | FX Vol Green | FX Vol Red | Inflation Red | Rationale |
|------|-------------|-----------|--------------|-----------|
| Nairobi KES | < 4% | > 8% | > 8% | Managed float — volatility is a safety valve |
| Baku AZN | < 1% | > 3% | > 12% | Hard peg at 1.70 — volatility is a leak in the dam |

> *"In a float, volatility is a safety valve; in a peg, it is a leak in the dam."* — Said Taghizade, KPMG Baku, March 2026

---

## Project Structure

```
frontier-market-regime/
├── src/
│   ├── engine/
│   │   └── regime_engine.py        # Core scoring engine
│   ├── collectors/
│   │   ├── cbk_collector.py        # Kenya FX via ExchangeRate-API
│   │   ├── cba_collector.py        # Azerbaijan CBA collector
│   │   └── nse_collector.py        # NSE capital flow signals
│   └── config.py                   # Market configurations
├── app/
│   ├── manual_entry.py             # Streamlit classification dashboard
│   └── dashboard.py                # Historical analysis dashboard
├── pipeline/
│   └── daily_update.py             # Automated daily pipeline
├── data/
│   ├── processed/                  # Daily CSVs + regime logs
│   └── logs/                       # Text reports
├── notebooks/                      # Research notebooks
├── .env.example                    # Required environment variables
└── requirements.txt
```

---

## Setup

### Prerequisites

- Python 3.10 or higher
- Git
- A RapidAPI account with the [Nairobi Stock Exchange API](https://rapidapi.com/lesanmax/api/nairobi-stock-exchange-nse) subscribed

### 1. Clone the repository

```bash
git clone https://github.com/witttingtorch/frontier-market-regime.git
cd frontier-market-regime
```

### 2. Create and activate virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux / Mac
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and add your key:

```
RAPIDAPI_KEY=your_rapidapi_key_here
```

### 5. Create required data directories

```bash
mkdir -p data/processed data/logs
```

### 6. Verify the engine works

```bash
python src/collectors/cbk_collector.py
```

You should see a live USD/KES rate around 129-133. No sample data warning means the pipeline is healthy.

### 7. Run the classification dashboard

```bash
streamlit run app/manual_entry.py
```

Opens at `http://localhost:8501`

### 8. Run the daily pipeline

```bash
python pipeline/daily_update.py
```

### 9. View historical analysis

```bash
streamlit run app/dashboard.py
```

Opens at `http://localhost:8502`

---

### Troubleshooting

**No module named 'src'** — make sure you are running commands from the project root, not from inside a subfolder.

**RAPIDAPI_KEY not set** — capital flow scoring will default to neutral (Z=0). All other variables will still work.

**Baku node errors** — expected if you are running from Nairobi. Run Nairobi only: `python pipeline/daily_update.py --markets nairobi`

---

## Daily Workflow

```
1. Open dashboard          streamlit run app/manual_entry.py
2. Fetch latest FX rate    Click "Fetch Latest FX Rates"
3. Update variables        FX vol, flows (daily)
                           Reserves, CPI (monthly on release)
4. Calculate regime        Click "Calculate Regime"
5. Review and save         Analysis tab → Save to CSV
6. Log observations        Logs tab → Street-level intelligence
7. Push to GitHub          git add -A && git commit && git push
```

---

## Research Log

| Date | Node | Regime | Score | Notes |
|------|------|--------|-------|-------|
| 2026-03-09 | Baku | 🟢 Risk-On | +5 | CBA cut to 6.5%, strong non-oil FDI. Geopolitical override flagged (Nakhchivan tensions) but not applied — no capital flight evidence. |
| 2026-03-10 | Nairobi | 🟡 Defensive | +2 | CBK cutting only strong green signal. Reserves declining, CPI above 5% threshold. |
| 2026-03-11 | Nairobi | 🟡 Defensive | +2 | Live FX pipeline operational. USD/KES: 129.16. |

---

## Working Paper

**Title:** *Hybrid Human-Quantitative Regime Detection in Frontier Markets: Evidence from East Africa and the Caucasus*

**Authors:** Moses Martin Njuguna Gikonyo (Nairobi node) · Said Taghizade (Baku node, KPMG)

**Target:** Finance Research Letters / Journal of Emerging Market Finance

**Timeline:**
- Q1-Q2 2026 — Data collection (both nodes logging)
- July 2026 — First draft
- September 2026 — Submission

---

## Requirements

```
streamlit
pandas
numpy
requests
beautifulsoup4
python-dotenv
matplotlib
```

---

## Environment Variables

```bash
# .env.example
RAPIDAPI_KEY=your_rapidapi_key_here   # NSE RapidAPI for capital flow data
```

---

## License

MIT License — open for academic use and extension to other frontier market nodes.

---

*Built in Nairobi. Calibrated in Baku. March 2026.*
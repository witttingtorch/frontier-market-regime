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

> _"Detection latency is social before it is statistical."_

---

## Live Nodes

| Market  | Currency | Central Bank | Status                     | Analyst              |
| ------- | -------- | ------------ | -------------------------- | -------------------- |
| Nairobi | KES      | CBK          | 🟢 Active — logging daily  | Moses Martin         |
| Baku    | AZN      | CBA          | 🟢 Active — logging weekly | Said Taghizade, KPMG |

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
│              SENTIMENT LAYER                         │
│                                                      │
│   Web scraping: Business Daily, CBK, Reuters RSS     │
│   Weighted keyword scoring (−3 to +3 per signal)    │
│   Kenya-filtered: KES, CBK, Nairobi, Shilling        │
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

| Node        | FX Vol Green | FX Vol Red | Inflation Red | Rationale                                          |
| ----------- | ------------ | ---------- | ------------- | -------------------------------------------------- |
| Nairobi KES | < 4%         | > 8%       | > 8%          | Managed float — volatility is a safety valve       |
| Baku AZN    | < 1%         | > 3%       | > 12%         | Hard peg at 1.70 — volatility is a leak in the dam |

> _"In a float, volatility is a safety valve; in a peg, it is a leak in the dam."_ — Said Taghizade, KPMG Baku, March 2026

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
│   │   ├── nse_collector.py        # NSE capital flow signals
│   │   └── sentiment_collector.py  # Web scraping + keyword scoring
│   └── config.py                   # Market configurations
├── app/
│   ├── manual_entry.py             # Streamlit classification dashboard
│   └── dashboard.py                # Historical analysis dashboard
├── pipeline/
│   ├── daily_update.py             # Automated daily pipeline
│   ├── sentiment_analysis.py       # Sentiment chart + markdown report
│   ├── alert_system.py             # Regime alert notifications
│   └── data_sync.py                # Data synchronisation utilities
├── data/
│   ├── processed/                  # Daily CSVs + regime logs
│   │   ├── nairobi_regime_log.csv
│   │   └── nairobi_sentiment_log.csv
│   └── logs/                       # Text reports + sentiment dashboard PNG
├── notebooks/                      # Research notebooks (01–05)
├── tests/                          # Pytest suite
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

You should see a live USD/KES rate around 129–133. No sample data warning means the pipeline is healthy.

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

### 10. Collect street-level sentiment

Scrapes Business Daily Africa, CBK, Reuters RSS, and The East African. Filters for Kenya-relevant headlines, scores them using a weighted keyword dictionary, and appends results to `data/processed/nairobi_sentiment_log.csv`.

```bash
python src/collectors/sentiment_collector.py
```

### 11. Run sentiment analysis report

Reads from `nairobi_sentiment_log.csv` and produces a multi-panel chart and markdown summary saved to `data/logs/`.

```bash
python pipeline/sentiment_analysis.py
```

---

## Sentiment Intelligence

The framework includes a two-script sentiment layer that scrapes street-level signals from financial news sources and produces a weighted daily score and visual report.

### Sources

| Source                      | Type       |
| --------------------------- | ---------- |
| Business Daily Africa       | Web scrape |
| Central Bank of Kenya (CBK) | Web scrape |
| Reuters Africa              | RSS feed   |
| The East African            | RSS feed   |

Articles are filtered to Kenya-relevant content using keywords: `kenya`, `kes`, `shilling`, `nairobi`, `cbk`, `central bank of kenya`, `kenyan`.

### Keyword Scoring

Each article is scored using a weighted keyword dictionary. Scores are additive across all matched keywords in a headline or snippet.

**Negative signals (examples):**

| Keyword                                               | Weight |
| ----------------------------------------------------- | ------ |
| `fuel shortage`, `dollar shortage`, `currency crisis` | −3     |
| `cbk intervene`, `forex pressure`, `hoarding`         | −2     |
| `depreciation`, `outflows`, `inflation surge`         | −1     |

**Positive signals (examples):**

| Keyword                                                          | Weight |
| ---------------------------------------------------------------- | ------ |
| `shilling gains`, `reserves increase`, `current account surplus` | +3     |
| `cbk comfortable`, `forex stable`, `rate cut`                    | +2     |
| `stable`, `inflows`, `recovery`, `investment`                    | +1     |

---

### Running the Sentiment Collector

`src/collectors/sentiment_collector.py` scrapes all sources, scores headlines, and appends results to `data/processed/nairobi_sentiment_log.csv`.

```bash
python src/collectors/sentiment_collector.py
```

**Expected output:**

```
Fetching Business Daily Africa...
Fetching CBK headlines...
Fetching Reuters RSS...
Fetching East African RSS...
Scored 14 Kenya-relevant articles.
Saved → data/processed/nairobi_sentiment_log.csv
```

Run this daily — ideally as part of the morning pipeline before opening the classification dashboard.

---

### Running the Sentiment Analysis Report

`pipeline/sentiment_analysis.py` reads from `data/processed/nairobi_sentiment_log.csv` and produces:

- A multi-panel chart saved to `data/logs/sentiment_dashboard.png`
- A markdown summary report saved to `data/logs/sentiment_report.md`

```bash
python pipeline/sentiment_analysis.py
```

**Expected output:**

```
Reading sentiment log → data/processed/nairobi_sentiment_log.csv
Generating charts...
Saved → data/logs/sentiment_dashboard.png
Saved → data/logs/sentiment_report.md
```

Open `data/logs/sentiment_dashboard.png` to review the visual. The markdown report is suitable for direct inclusion in research notes or the working paper appendix.

---

### Recommended Sentiment Workflow

```
1. Run collector       python src/collectors/sentiment_collector.py
2. Run analysis        python pipeline/sentiment_analysis.py
3. Review chart        open data/logs/sentiment_dashboard.png
4. Review report       cat data/logs/sentiment_report.md
5. Open dashboard      streamlit run app/manual_entry.py
6. Log observations    Logs tab → flag any high-scoring signals
7. Push to GitHub      git add -A && git commit && git push
```

> Sentiment scores should inform — not override — the quantitative regime score. Use the human layer to reconcile large divergences between the two.

---

### Troubleshooting

**No articles returned** — check your internet connection. RSS feeds from Reuters or The East African may occasionally be unavailable; the script will skip failed sources and continue.

**`nairobi_sentiment_log.csv` not found** — run the collector at least once before running the analysis script.

**Matplotlib display errors** — if running on a headless server, the chart will still save to `data/logs/` even without a display; ignore any `UserWarning` from matplotlib.

---

## Daily Workflow (Full Pipeline)

```
1. Run sentiment collector    python src/collectors/sentiment_collector.py
2. Run sentiment analysis     python pipeline/sentiment_analysis.py
3. Open dashboard             streamlit run app/manual_entry.py
4. Fetch latest FX rate       Click "Fetch Latest FX Rates"
5. Update variables           FX vol, flows (daily)
                              Reserves, CPI (monthly on release)
6. Calculate regime           Click "Calculate Regime"
7. Review and save            Analysis tab → Save to CSV
8. Log observations           Logs tab → Street-level intelligence
9. Push to GitHub             git add -A && git commit && git push
```

---

## Troubleshooting

**No module named 'src'** — make sure you are running commands from the project root, not from inside a subfolder.

**RAPIDAPI_KEY not set** — capital flow scoring will default to neutral (Z=0). All other variables will still work.

**Baku node errors** — expected if you are running from Nairobi. Run Nairobi only: `python pipeline/daily_update.py --markets nairobi`

---

## Research Log

| Date       | Node    | Regime       | Score | Notes                                                                                                                                  |
| ---------- | ------- | ------------ | ----- | -------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-03-09 | Baku    | 🟢 Risk-On   | +5    | CBA cut to 6.5%, strong non-oil FDI. Geopolitical override flagged (Nakhchivan tensions) but not applied — no capital flight evidence. |
| 2026-03-10 | Nairobi | 🟡 Defensive | +2    | CBK cutting only strong green signal. Reserves declining, CPI above 5% threshold.                                                      |
| 2026-03-11 | Nairobi | 🟡 Defensive | +2    | Live FX pipeline operational. USD/KES: 129.16.                                                                                         |

---

## Working Paper

**Title:** _Hybrid Human-Quantitative Regime Detection in Frontier Markets: Evidence from East Africa and the Caucasus_

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
feedparser
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

_Built in Nairobi. Calibrated in Baku. March 2026._

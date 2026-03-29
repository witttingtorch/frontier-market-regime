"""
Sentiment Analysis Script — Kenya Market Monitoring
Reads from: data/processed/nairobi_sentiment_log.csv
Outputs:    charts, summary stats, and a markdown report
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path
from collections import Counter
import warnings

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "data" / "logs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Load data ─────────────────────────────────────────────────────────────────
def load_data(path: Path = DATA_DIR / "nairobi_sentiment_log.csv") -> pd.DataFrame:
    """Load and clean the sentiment log."""
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["sentiment_score"] = pd.to_numeric(df["sentiment_score"], errors="coerce").fillna(0)

    def classify_topic(src: str) -> str:
        src = str(src).lower()
        if "fuel" in src:
            return "Fuel"
        if "inflation" in src:
            return "Inflation"
        if "economy" in src:
            return "Economy"
        if "monetary" in src or "cbk" in src:
            return "CBK Policy"
        if "business daily" in src:
            return "Business Daily"
        return "Other"

    df["topic"] = df["source"].apply(classify_topic)
    return df


# ── Signal parsing ────────────────────────────────────────────────────────────
def parse_signals(df: pd.DataFrame) -> Counter:
    """Flatten and count all individual signals detected."""
    sig_col = "signals_detected" if "signals_detected" in df.columns else "signals"
    counter: Counter = Counter()
    for val in df[sig_col].dropna():
        for sig in str(val).split(","):
            sig = sig.strip().lower()
            if sig:
                counter[sig] += 1
    return counter


# ── Summary statistics ────────────────────────────────────────────────────────
def summary_stats(df: pd.DataFrame) -> dict:
    """Return a dict of headline stats."""
    pos = (df["sentiment_score"] > 0).sum()
    neu = (df["sentiment_score"] == 0).sum()
    neg = (df["sentiment_score"] < 0).sum()
    total = len(df)

    by_topic = (
        df.groupby("topic")["sentiment_score"]
        .agg(["mean", "std", "count"])
        .rename(columns={"mean": "avg_score", "std": "std_score", "count": "n_records"})
        .round(3)
    )

    return {
        "total_records": total,
        "avg_sentiment": round(df["sentiment_score"].mean(), 3),
        "median_sentiment": round(df["sentiment_score"].median(), 3),
        "positive_pct": round(pos / total * 100, 1),
        "neutral_pct": round(neu / total * 100, 1),
        "negative_pct": round(neg / total * 100, 1),
        "by_topic": by_topic,
        "date_range": (df["date"].min().date(), df["date"].max().date()),
    }


# ── Plotting ──────────────────────────────────────────────────────────────────
COLORS = {
    "Fuel":          "#E24B4A",
    "Inflation":     "#639922",
    "Economy":       "#378ADD",
    "CBK Policy":    "#BA7517",
    "Business Daily":"#7F77DD",
    "Other":         "#888780",
}

SENTIMENT_COLORS = {
    "positive": "#639922",
    "neutral":  "#888780",
    "negative": "#E24B4A",
}


def plot_dashboard(df: pd.DataFrame, signals: Counter, stats: dict, out_path: Path):
    """Produce a 2x3 dashboard figure and save to out_path."""
    fig = plt.figure(figsize=(16, 12), facecolor="white")
    fig.suptitle(
        f"Kenya Market Sentiment — {stats['date_range'][0]} to {stats['date_range'][1]}",
        fontsize=15,
        fontweight="bold",
        y=0.98,
    )
    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

    # 1 ── Sentiment distribution (pie)
    ax1 = fig.add_subplot(gs[0, 0])
    sizes = [stats["positive_pct"], stats["neutral_pct"], stats["negative_pct"]]
    labels = [
        f"Positive\n{stats['positive_pct']}%",
        f"Neutral\n{stats['neutral_pct']}%",
        f"Negative\n{stats['negative_pct']}%",
    ]
    ax1.pie(
        sizes,
        labels=labels,
        colors=[SENTIMENT_COLORS["positive"], SENTIMENT_COLORS["neutral"], SENTIMENT_COLORS["negative"]],
        startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
        textprops={"fontsize": 9},
    )
    ax1.set_title("Sentiment distribution", fontsize=11, pad=10)

    # 2 ── Average score by topic (bar)
    ax2 = fig.add_subplot(gs[0, 1])
    by_topic = stats["by_topic"].sort_values("avg_score")
    colors = [COLORS.get(t, "#888780") for t in by_topic.index]
    bars = ax2.barh(by_topic.index, by_topic["avg_score"], color=colors, edgecolor="white", height=0.55)
    ax2.axvline(0, color="#ccc", linewidth=0.8, linestyle="--")
    for bar, val in zip(bars, by_topic["avg_score"]):
        ax2.text(
            val + (0.05 if val >= 0 else -0.05),
            bar.get_y() + bar.get_height() / 2,
            f"{val:+.2f}",
            va="center",
            ha="left" if val >= 0 else "right",
            fontsize=8,
            color="#444",
        )
    ax2.set_title("Avg sentiment by topic", fontsize=11)
    ax2.set_xlabel("Average score", fontsize=9)
    ax2.tick_params(labelsize=9)
    ax2.spines[["top", "right"]].set_visible(False)

    # 3 ── Top 10 signals (horizontal bar)
    ax3 = fig.add_subplot(gs[0, 2])
    neg_signals = {"fuel shortage", "shortage", "hoarding", "rationing", "depreciation", "pressure", "intervention"}
    top_sigs = signals.most_common(10)
    sig_labels = [s[0] for s in top_sigs][::-1]
    sig_vals = [s[1] for s in top_sigs][::-1]
    sig_colors = [SENTIMENT_COLORS["negative"] if s in neg_signals else SENTIMENT_COLORS["positive"] for s in sig_labels]
    ax3.barh(sig_labels, sig_vals, color=sig_colors, edgecolor="white", height=0.6)
    ax3.set_title("Top 10 signals detected", fontsize=11)
    ax3.set_xlabel("Frequency", fontsize=9)
    ax3.tick_params(labelsize=8)
    ax3.spines[["top", "right"]].set_visible(False)

    # 4 ── Daily trend by topic (line)
    ax4 = fig.add_subplot(gs[1, :2])
    daily = df.groupby(["date", "topic"])["sentiment_score"].mean().reset_index()
    for topic, grp in daily.groupby("topic"):
        if topic in ("Other", "African Business", "CBK Press Release"):
            continue
        grp = grp.sort_values("date")
        ax4.plot(
            grp["date"],
            grp["sentiment_score"],
            marker="o",
            markersize=5,
            linewidth=1.8,
            label=topic,
            color=COLORS.get(topic, "#888780"),
        )
    ax4.axhline(0, color="#ddd", linewidth=0.8, linestyle="--")
    ax4.set_title("Daily average sentiment by topic", fontsize=11)
    ax4.set_ylabel("Avg score", fontsize=9)
    ax4.legend(fontsize=8, loc="upper left", framealpha=0.6)
    ax4.tick_params(labelsize=8)
    ax4.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b %d"))
    ax4.spines[["top", "right"]].set_visible(False)

    # 5 ── Score distribution histogram
    ax5 = fig.add_subplot(gs[1, 2])
    ax5.hist(
        df["sentiment_score"],
        bins=range(int(df["sentiment_score"].min()) - 1, int(df["sentiment_score"].max()) + 2),
        color="#378ADD",
        edgecolor="white",
        rwidth=0.75,
    )
    ax5.axvline(stats["avg_sentiment"], color="#E24B4A", linewidth=1.5, linestyle="--", label=f"Mean {stats['avg_sentiment']}")
    ax5.set_title("Score distribution", fontsize=11)
    ax5.set_xlabel("Sentiment score", fontsize=9)
    ax5.set_ylabel("Count", fontsize=9)
    ax5.legend(fontsize=8)
    ax5.tick_params(labelsize=8)
    ax5.spines[["top", "right"]].set_visible(False)

    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"[✓] Dashboard saved → {out_path}")


# ── Markdown report ───────────────────────────────────────────────────────────
def write_report(stats: dict, signals: Counter, out_path: Path):
    """Write a concise markdown summary."""
    lines = [
        "# Kenya Market Sentiment Report",
        f"**Period:** {stats['date_range'][0]} to {stats['date_range'][1]}  ",
        f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Headline figures",
        "| Metric | Value |",
        "|---|---|",
        f"| Total records | {stats['total_records']} |",
        f"| Average sentiment | {stats['avg_sentiment']} |",
        f"| Median sentiment | {stats['median_sentiment']} |",
        f"| Positive | {stats['positive_pct']}% |",
        f"| Neutral | {stats['neutral_pct']}% |",
        f"| Negative | {stats['negative_pct']}% |",
        "",
        "## Average sentiment by topic",
        stats["by_topic"].to_markdown(),
        "",
        "## Top 15 signals",
        "| Signal | Count | Polarity |",
        "|---|---|---|",
    ]
    neg_sigs = {"fuel shortage", "shortage", "hoarding", "rationing", "depreciation", "pressure", "intervention"}
    for sig, cnt in signals.most_common(15):
        polarity = "🔴 Negative" if sig in neg_sigs else "🟢 Positive"
        lines.append(f"| {sig} | {cnt} | {polarity} |")

    lines += [
        "",
        "## Key observations",
        "- **Fuel** coverage is the most negative topic, driven by shortage and hoarding signals.",
        "- **CBK Monetary Policy** is the most positive source, consistently emphasising stability, growth, and investment.",
        "- **Inflation** sentiment is broadly neutral-to-positive, reflecting easing consumer prices.",
        "- **Economy/Forex** coverage is net positive, anchored by a stable shilling and rising reserves.",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[✓] Report saved → {out_path}")


# ── Street-Level Intelligence Summary ─────────────────────────────────────────
def street_intelligence_summary(stats: dict, signals: Counter) -> str:
    """
    Generate a street-level intelligence string ready to paste into
    the dashboard's 'Add Street-Level Observation' text area.
    """
    by_topic = stats["by_topic"]
    top_neg = signals.most_common(20)
    neg_sigs = {"fuel shortage", "shortage", "hoarding", "rationing",
                "depreciation", "pressure", "intervention"}
    pos_sigs = {"stable", "growth", "investment", "inflows",
                "reserves increase", "liquidity", "surplus", "rallies"}

    neg_found = [s for s, _ in top_neg if s in neg_sigs][:3]
    pos_found = [s for s, _ in top_neg if s in pos_sigs][:3]

    worst_topic = by_topic["avg_score"].idxmin()
    worst_score = by_topic.loc[worst_topic, "avg_score"]
    best_topic = by_topic["avg_score"].idxmax()
    best_score = by_topic.loc[best_topic, "avg_score"]

    neg_str = ", ".join(neg_found) if neg_found else "none detected"
    pos_str = ", ".join(pos_found) if pos_found else "none detected"

    summary = (
        f"Sentiment scan {stats['date_range'][0]} to {stats['date_range'][1]} "
        f"({stats['total_records']} records). "
        f"Overall avg: {stats['avg_sentiment']:+.2f} | "
        f"Pos {stats['positive_pct']}% / Neu {stats['neutral_pct']}% / Neg {stats['negative_pct']}%. "
        f"Weakest topic: {worst_topic} (avg {worst_score:+.2f}) — "
        f"stress signals: {neg_str}. "
        f"Strongest topic: {best_topic} (avg {best_score:+.2f}) — "
        f"positive signals: {pos_str}."
    )
    return summary


# ── Main ──────────────────────────────────────────────────────────────────────
def run(csv_path: Path | None = None):
    csv_path = csv_path or DATA_DIR / "nairobi_sentiment_log.csv"

    print(f"Loading data from {csv_path} ...")
    df = load_data(csv_path)
    print(f"  {len(df)} rows, {df['date'].nunique()} unique dates, topics: {sorted(df['topic'].unique())}")

    signals = parse_signals(df)
    stats = summary_stats(df)

    print("\n── Headline stats ──────────────────────────────")
    print(f"  Total records : {stats['total_records']}")
    print(f"  Avg sentiment : {stats['avg_sentiment']}")
    print(f"  Positive      : {stats['positive_pct']}%")
    print(f"  Neutral       : {stats['neutral_pct']}%")
    print(f"  Negative      : {stats['negative_pct']}%")
    print("\n── Topic averages ──────────────────────────────")
    print(stats["by_topic"].to_string())
    print("\n── Top 10 signals ──────────────────────────────")
    for sig, cnt in signals.most_common(10):
        print(f"  {cnt:>4}  {sig}")

    plot_dashboard(
        df, signals, stats,
        out_path=OUTPUT_DIR / "sentiment_dashboard.png",
    )
    write_report(
        stats, signals,
        out_path=OUTPUT_DIR / "sentiment_report.md",
    )

    summary = street_intelligence_summary(stats, signals)
    print("\n── Street Intelligence (copy → dashboard) ──────")
    print(summary)

    return df, stats, signals


if __name__ == "__main__":
    run()
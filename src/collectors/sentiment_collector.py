"""
Street-level sentiment collector via web scraping.
Scrapes Business Daily, CBK press releases, EPRA fuel prices.
"""

import requests
from bs4 import BeautifulSoup
import feedparser
import pandas as pd
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

# ── Keyword signals ───────────────────────────────────────────────────────────

NEGATIVE_KEYWORDS = [
    'shortage', 'hoarding', 'intervention', 'pressure', 'depreciation',
    'outflows', 'deficit', 'delay', 'congestion', 'inflation surge',
    'fuel shortage', 'dollar shortage', 'forex pressure', 'cbk intervene',
    'import delays', 'supply disruption', 'rationing'
]

POSITIVE_KEYWORDS = [
    'surplus', 'inflows', 'appreciation', 'stable', 'reserves increase',
    'dollar supply', 'liquidity', 'growth', 'investment', 'recovery',
    'forex stable', 'shilling gains', 'cbk comfortable'
]


def score_text(text: str) -> tuple:
    """Score text for sentiment. Returns (score, matched_keywords)."""
    text_lower = text.lower()
    neg = [k for k in NEGATIVE_KEYWORDS if k in text_lower]
    pos = [k for k in POSITIVE_KEYWORDS if k in text_lower]
    score = len(pos) - len(neg)
    matched = pos + neg
    return score, matched


# ── Scrapers ──────────────────────────────────────────────────────────────────

def scrape_business_daily() -> list:
    """Scrape Business Daily Africa currencies section."""
    results = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(
            "https://www.businessdailyafrica.com/bd/markets/currencies",
            headers=headers, timeout=15
        )
        soup = BeautifulSoup(r.content, 'html.parser')

        # Extract headlines
        headlines = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            text = tag.get_text(strip=True)
            if len(text) > 20:
                headlines.append(text)

        for headline in headlines[:10]:
            score, matched = score_text(headline)
            if matched:
                results.append({
                    'source': 'Business Daily Africa',
                    'text': headline,
                    'sentiment_score': score,
                    'signals_detected': ', '.join(matched)
                })

        logger.info(f"Business Daily: {len(results)} signals found")

    except Exception as e:
        logger.warning(f"Business Daily scrape failed: {e}")

    return results


def scrape_cbk_press_releases() -> list:
    """Scrape CBK press releases page."""
    results = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(
            "https://www.centralbank.go.ke/press-releases/",
            headers=headers, timeout=15
        )
        soup = BeautifulSoup(r.content, 'html.parser')

        for tag in soup.find_all(['h2', 'h3', 'a']):
            text = tag.get_text(strip=True)
            if len(text) > 20:
                score, matched = score_text(text)
                results.append({
                    'source': 'CBK Press Release',
                    'text': text,
                    'sentiment_score': score,
                    'signals_detected': ', '.join(matched) if matched else ''
                })

        # Most recent 5 only
        results = results[:5]
        logger.info(f"CBK: {len(results)} releases found")

    except Exception as e:
        logger.warning(f"CBK scrape failed: {e}")

    return results


def scrape_rss_feeds() -> list:
    """Scrape RSS feeds for Kenya financial news."""
    results = []

    feeds = [
        ("Reuters Africa", "https://feeds.reuters.com/reuters/AFRICANews"),
        ("The East African", "https://www.theeastafrican.co.ke/tea/rss"),
    ]

    for source_name, feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                title = entry.get('title', '')
                summary = entry.get('summary', '')
                text = f"{title} {summary}"

                # Only Kenya/FX relevant entries
                if any(k in text.lower() for k in ['kenya', 'kes', 'shilling', 'nairobi', 'cbk']):
                    score, matched = score_text(text)
                    results.append({
                        'source': source_name,
                        'text': title,
                        'sentiment_score': score,
                        'signals_detected': ', '.join(matched) if matched else ''
                    })

            logger.info(f"{source_name}: {len(results)} relevant entries")

        except Exception as e:
            logger.warning(f"{source_name} RSS failed: {e}")

    return results


# ── Main collector ────────────────────────────────────────────────────────────

def collect_sentiment(save: bool = True) -> pd.DataFrame:
    """
    Run all scrapers, combine results, save to CSV.
    Called by daily_update.py every morning.
    """
    logger.info("Starting sentiment collection...")

    all_results = []
    all_results.extend(scrape_business_daily())
    all_results.extend(scrape_cbk_press_releases())
    all_results.extend(scrape_rss_feeds())

    if not all_results:
        logger.warning("No sentiment data collected")
        return pd.DataFrame()

    df = pd.DataFrame(all_results)
    df['date'] = datetime.now().strftime('%Y-%m-%d')
    df['timestamp'] = datetime.now().isoformat()
    df['market'] = 'nairobi'

    # Daily aggregate score
    daily_score = df['sentiment_score'].sum()
    logger.info(f"Daily sentiment score: {daily_score:+d} from {len(df)} signals")

    if save:
        os.makedirs('data/processed', exist_ok=True)
        path = 'data/processed/nairobi_sentiment_log.csv'
        try:
            existing = pd.read_csv(path)
            updated = pd.concat([existing, df], ignore_index=True)
        except FileNotFoundError:
            updated = df
        updated.to_csv(path, index=False)
        logger.info(f"Saved {len(df)} records to {path}")

    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df = collect_sentiment()
    if not df.empty:
        print(f"\nCollected {len(df)} signals")
        print(f"Daily score: {df['sentiment_score'].sum():+d}")
        print("\nTop signals:")
        print(df[['source', 'text', 'sentiment_score', 'signals_detected']].to_string())

"""
Street-level sentiment collector via web scraping.
Sources: Business Daily Africa, CBK, Reuters RSS, East African RSS
"""

import requests
from bs4 import BeautifulSoup
import feedparser
import pandas as pd
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

# Weighted keyword dicts
NEGATIVE_KEYWORDS = {
    'fuel shortage':       -3,
    'dollar shortage':     -3,
    'forex crunch':        -3,
    'currency crisis':     -3,
    'capital flight':      -3,
    'debt distress':       -3,
    'cbk intervene':       -2,
    'forex pressure':      -2,
    'hoarding':            -2,
    'supply disruption':   -2,
    'rationing':           -2,
    'shortage':            -1,
    'depreciation':        -1,
    'outflows':            -1,
    'import delays':       -1,
    'weakens':             -1,
    'slumps':              -1,
    'inflation surge':     -1,
    'intervention':        -1,
    'pressure':            -1,
    'deficit':             -1,
    'delay':               -1,
    'congestion':          -1,
}

POSITIVE_KEYWORDS = {
    'shilling gains':           3,
    'reserves increase':        3,
    'current account surplus':  3,
    'cbk comfortable':          2,
    'forex stable':             2,
    'rallies':                  2,
    'strengthens':              2,
    'appreciation':             2,
    'rate cut':                 2,
    'easing':                   2,
    'surplus':                  1,
    'inflows':                  1,
    'stable':                   1,
    'liquidity':                1,
    'recovery':                 1,
    'confidence':               1,
    'growth':                   1,
    'investment':               1,
}

KENYA_KEYWORDS = [
    'kenya', 'kes', 'shilling', 'nairobi', 'cbk',
    'central bank of kenya', 'kenyan'
]


def score_text(text: str) -> tuple:
    text_lower = text.lower()
    neg = {k: v for k, v in NEGATIVE_KEYWORDS.items() if k in text_lower}
    pos = {k: v for k, v in POSITIVE_KEYWORDS.items() if k in text_lower}
    score = sum(pos.values()) + sum(neg.values())
    return score, list(pos.keys()) + list(neg.keys())


def is_kenya_relevant(text: str) -> bool:
    text_lower = text.lower()
    return any(k in text_lower for k in KENYA_KEYWORDS)


def scrape_business_daily() -> list:
    """Scrape Business Daily Africa — currencies and markets sections."""
    results = []
    urls = [
        "https://www.businessdailyafrica.com/bd/markets/currencies",
        "https://www.businessdailyafrica.com/bd/economy"
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    }

    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(r.content, 'html.parser')

            # Target article headlines specifically
            for tag in soup.find_all(['h1', 'h2', 'h3'], class_=lambda c: c and
                any(x in str(c).lower() for x in ['title', 'headline', 'article', 'story'])):
                text = tag.get_text(strip=True)
                if len(text) > 25:
                    score, matched = score_text(text)
                    results.append({
                        'source': 'Business Daily Africa',
                        'text': text,
                        'sentiment_score': score,
                        'signals_detected': ', '.join(matched)
                    })

            # Also grab plain article links as fallback
            for a in soup.find_all('a', href=True):
                text = a.get_text(strip=True)
                if len(text) > 30 and is_kenya_relevant(text):
                    score, matched = score_text(text)
                    results.append({
                        'source': 'Business Daily Africa',
                        'text': text,
                        'sentiment_score': score,
                        'signals_detected': ', '.join(matched)
                    })

            logger.info(f"Business Daily ({url}): {len(results)} items")

        except Exception as e:
            logger.warning(f"Business Daily scrape failed ({url}): {e}")

    # Deduplicate
    seen = set()
    unique = []
    for r in results:
        if r['text'] not in seen:
            seen.add(r['text'])
            unique.append(r)

    return unique[:15]


def scrape_cbk_mpc() -> list:
    """Scrape CBK MPC decisions and monetary policy statements."""
    results = []
    urls = [
        "https://www.centralbank.go.ke/monetary-policy/",
        "https://www.centralbank.go.ke/monetary-policy-statements/"
    ]

    headers = {'User-Agent': 'Mozilla/5.0'}

    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(r.content, 'html.parser')

            # Look for actual content links — not nav elements
            main = soup.find('main') or soup.find('div', class_=lambda c: c and
                any(x in str(c).lower() for x in ['content', 'main', 'article', 'post']))

            if main:
                for tag in main.find_all(['h2', 'h3', 'h4', 'p', 'a']):
                    text = tag.get_text(strip=True)
                    if len(text) > 30 and not any(nav in text.lower() for nav in
                        ['navigation', 'menu', 'cookie', 'subscribe', 'login']):
                        score, matched = score_text(text)
                        results.append({
                            'source': 'CBK Monetary Policy',
                            'text': text[:200],
                            'sentiment_score': score,
                            'signals_detected': ', '.join(matched)
                        })

            logger.info(f"CBK ({url}): {len(results)} items")

        except Exception as e:
            logger.warning(f"CBK scrape failed ({url}): {e}")

    return results[:5]


def scrape_rss_feeds() -> list:
    """Scrape RSS feeds filtering for Kenya-relevant content."""
    results = []

    feeds = [
        ("Google News Kenya Economy", "https://news.google.com/rss/search?q=kenya+shilling+forex+CBK&hl=en-KE&gl=KE&ceid=KE:en"),
        ("Google News Kenya Fuel", "https://news.google.com/rss/search?q=kenya+fuel+shortage+prices&hl=en-KE&gl=KE&ceid=KE:en"),
        ("Google News Kenya Inflation", "https://news.google.com/rss/search?q=kenya+inflation+economy&hl=en-KE&gl=KE&ceid=KE:en"),
        ("Reuters Africa", "https://feeds.reuters.com/reuters/AFRICANews"),
        ("The East African", "https://www.theeastafrican.co.ke/tea/rss"),
        ("African Business", "https://african.business/feed"),
    ]

    for source_name, feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            count = 0

            for entry in feed.entries[:20]:
                title = entry.get('title', '')
                summary = entry.get('summary', '')
                text = f"{title} {summary}"

                if is_kenya_relevant(text):
                    score, matched = score_text(text)
                    results.append({
                        'source': source_name,
                        'text': title,
                        'sentiment_score': score,
                        'signals_detected': ', '.join(matched)
                    })
                    count += 1

            logger.info(f"{source_name}: {count} Kenya-relevant entries")

        except Exception as e:
            logger.warning(f"{source_name} RSS failed: {e}")

    return results


def scrape_epra_fuel() -> list:
    """Check EPRA for fuel price changes — proxy for FX pass-through."""
    results = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(
            "https://www.epra.go.ke/petroleum/petroleum-prices/",
            headers=headers, timeout=15
        )
        soup = BeautifulSoup(r.content, 'html.parser')

        # Look for price tables or recent announcements
        for tag in soup.find_all(['h2', 'h3', 'td', 'p']):
            text = tag.get_text(strip=True)
            if any(k in text.lower() for k in ['petrol', 'diesel', 'kerosene', 'price', 'fuel']):
                if len(text) > 15:
                    score, matched = score_text(text)
                    results.append({
                        'source': 'EPRA Fuel Prices',
                        'text': text[:150],
                        'sentiment_score': score,
                        'signals_detected': ', '.join(matched)
                    })

        logger.info(f"EPRA: {len(results)} fuel price items")

    except Exception as e:
        logger.warning(f"EPRA scrape failed: {e}")

    return results[:3]


def collect_sentiment(save: bool = True) -> pd.DataFrame:
    """
    Run all scrapers, combine, score, save.
    Called by daily_update.py every morning.
    """
    logger.info("Starting sentiment collection...")

    all_results = []
    all_results.extend(scrape_business_daily())
    all_results.extend(scrape_cbk_mpc())
    all_results.extend(scrape_rss_feeds())
    all_results.extend(scrape_epra_fuel())

    if not all_results:
        logger.warning("No sentiment data collected from any source")
        return pd.DataFrame()

    df = pd.DataFrame(all_results)
    df['date'] = datetime.now().strftime('%Y-%m-%d')
    df['timestamp'] = datetime.now().isoformat()
    df['market'] = 'nairobi'

    # Remove empty/junk rows
    df = df[df['text'].str.len() > 15].reset_index(drop=True)

    daily_score = df['sentiment_score'].sum()
    signal_count = df[df['signals_detected'] != ''].shape[0]

    logger.info(f"Daily sentiment: {daily_score:+d} | Signal rows: {signal_count} / {len(df)}")

    if save:
        os.makedirs('data/processed', exist_ok=True)
        path = 'data/processed/nairobi_sentiment_log.csv'
        try:
            existing = pd.read_csv(path)
            updated = pd.concat([existing, df], ignore_index=True)
        except FileNotFoundError:
            updated = df
        updated.to_csv(path, index=False)
        logger.info(f"Saved to {path}")

    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df = collect_sentiment()
    if not df.empty:
        print(f"\n{'='*60}")
        print(f"Collected {len(df)} items | Daily score: {df['sentiment_score'].sum():+d}")
        print(f"{'='*60}")
        # Show only rows with actual signals
        signal_rows = df[df['signals_detected'] != '']
        if not signal_rows.empty:
            print("\nSignal rows:")
            print(signal_rows[['source', 'text', 'sentiment_score', 'signals_detected']].to_string())
        else:
            print("\nNo keyword signals detected today — neutral sentiment")
            print("\nSample headlines collected:")
            print(df[['source', 'text']].head(10).to_string())

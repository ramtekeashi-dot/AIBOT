"""News sentiment analysis using FinBERT with multi-source headline fetching."""

import time
import threading
import requests
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from config import FINBERT_MODEL, MAX_NEWS_HEADLINES

# Only include news from the last 30 days
_NEWS_MAX_AGE_DAYS = 30

# Lazy-load the pipeline to avoid slow imports at startup
_sentiment_pipeline = None
_pipeline_lock = threading.Lock()

# Reusable session for connection pooling
_http_session = None


def _get_pipeline():
    """Lazy-load FinBERT sentiment pipeline (thread-safe singleton)."""
    global _sentiment_pipeline
    if _sentiment_pipeline is not None:
        return _sentiment_pipeline
    with _pipeline_lock:
        # Double-check after acquiring lock (another thread may have loaded it)
        if _sentiment_pipeline is None:
            print("[INFO] Loading FinBERT model (first time may take a while)...")
            from transformers import pipeline
            _sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=FINBERT_MODEL,
                tokenizer=FINBERT_MODEL,
                top_k=None,
            )
    return _sentiment_pipeline


def preload_model():
    """Pre-load FinBERT model before multi-threaded analysis. Call once from main thread."""
    _get_pipeline()


def _get_session() -> requests.Session:
    """Get or create a reusable HTTP session."""
    global _http_session
    if _http_session is None:
        _http_session = requests.Session()
        _http_session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
    return _http_session


def _is_within_date_limit(item) -> bool:
    """Check if an RSS item's pubDate is within the last N days."""
    pub_date_tag = item.find("pubDate")
    if not pub_date_tag or not pub_date_tag.text:
        return True  # If no date, include by default
    try:
        pub_date = parsedate_to_datetime(pub_date_tag.text.strip())
        cutoff = datetime.now(timezone.utc) - timedelta(days=_NEWS_MAX_AGE_DAYS)
        return pub_date >= cutoff
    except Exception:
        return True  # If date parsing fails, include the headline


def _extract_items_with_urls(items, max_items: int) -> list[dict]:
    """Extract headline + URL from RSS items, filtered by date."""
    results = []
    for item in items:
        if not _is_within_date_limit(item):
            continue
        title_tag = item.find("title")
        link_tag = item.find("link")
        if title_tag and title_tag.text:
            headline = title_tag.text.strip()
            url = ""
            if link_tag:
                # Some RSS feeds put URL in tag text, others in next sibling
                url = link_tag.text.strip() if link_tag.text else ""
                if not url and link_tag.next_sibling:
                    url = str(link_tag.next_sibling).strip()
            results.append({"headline": headline, "url": url})
        if len(results) >= max_items:
            break
    return results


def _fetch_google_news_rss(query: str, max_items: int) -> list[dict]:
    """Fetch headlines+URLs from Google News RSS (filtered to last 30 days)."""
    url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        session = _get_session()
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "xml")
        items = soup.find_all("item", limit=max_items * 3)
        return _extract_items_with_urls(items, max_items)
    except Exception:
        return []


def _fetch_bing_news_rss(query: str, max_items: int) -> list[dict]:
    """Fetch headlines+URLs from Bing News RSS (fallback, filtered to last 30 days)."""
    url = f"https://www.bing.com/news/search?q={quote_plus(query)}&format=rss"
    try:
        session = _get_session()
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "xml")
        items = soup.find_all("item", limit=max_items * 3)
        return _extract_items_with_urls(items, max_items)
    except Exception:
        return []


def _scrape_et_search(symbol: str, max_items: int) -> list[dict]:
    """Scrape Economic Times search results for stock-specific headlines."""
    url = f"https://economictimes.indiatimes.com/search?q={quote_plus(symbol)}&type=news"
    try:
        session = _get_session()
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        # ET search results are in anchor tags within search result divs
        for a_tag in soup.select("a.flt"):
            headline = a_tag.get_text(strip=True)
            href = a_tag.get("href", "")
            if headline and len(headline) > 15:
                full_url = f"https://economictimes.indiatimes.com{href}" if href.startswith("/") else href
                results.append({"headline": headline, "url": full_url})
            if len(results) >= max_items:
                break
        # Fallback: try other common selectors
        if not results:
            for a_tag in soup.select(".search-result a, .eachStory h3 a, .article-list a"):
                headline = a_tag.get_text(strip=True)
                href = a_tag.get("href", "")
                if headline and len(headline) > 15:
                    full_url = f"https://economictimes.indiatimes.com{href}" if href.startswith("/") else href
                    results.append({"headline": headline, "url": full_url})
                if len(results) >= max_items:
                    break
        return results
    except Exception:
        return []


def _scrape_moneycontrol_search(symbol: str, max_items: int) -> list[dict]:
    """Scrape Moneycontrol search results for stock-specific headlines."""
    url = f"https://www.moneycontrol.com/news/tags/{quote_plus(symbol.lower())}.html"
    try:
        session = _get_session()
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for a_tag in soup.select("h2 a, .article_box h3 a, li.clearfix h2 a"):
            headline = a_tag.get_text(strip=True)
            href = a_tag.get("href", "")
            if headline and len(headline) > 15:
                results.append({"headline": headline, "url": href})
            if len(results) >= max_items:
                break
        return results
    except Exception:
        return []


def _scrape_livemint_search(symbol: str, max_items: int) -> list[dict]:
    """Scrape LiveMint search results for stock-specific headlines."""
    url = f"https://www.livemint.com/search?q={quote_plus(symbol)}&type=stories"
    try:
        session = _get_session()
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for a_tag in soup.select("h2 a, .headline a, .listingNew a"):
            headline = a_tag.get_text(strip=True)
            href = a_tag.get("href", "")
            if headline and len(headline) > 15:
                full_url = f"https://www.livemint.com{href}" if href.startswith("/") else href
                results.append({"headline": headline, "url": full_url})
            if len(results) >= max_items:
                break
        return results
    except Exception:
        return []


def fetch_news_headlines(symbol: str, max_items: int = MAX_NEWS_HEADLINES) -> list[dict]:
    """
    Fetch recent news headlines + URLs for an NSE stock.
    Uses 5 strategies with cascading fallback:
    1. Google News RSS (broad reach, multiple queries)
    2. Bing News RSS (different index)
    3. Economic Times search (Indian financial, stock-specific)
    4. Moneycontrol tag page (Indian financial, stock-specific)
    5. LiveMint search (Indian financial, stock-specific)
    Returns list of dicts: [{"headline": str, "url": str}, ...]
    """
    # Strategy 1: Google News RSS with multiple query patterns
    search_queries = [
        f"{symbol} NSE share price",
        f"{symbol} stock India",
        f'"{symbol}" NSE stock market',
    ]

    for query in search_queries:
        results = _fetch_google_news_rss(query, max_items)
        if results:
            return results
        time.sleep(0.3)

    # Strategy 2: Bing News RSS (wider index, different ranking)
    for query in [f"{symbol} NSE stock news", f"{symbol} share price India"]:
        results = _fetch_bing_news_rss(query, max_items)
        if results:
            return results
        time.sleep(0.3)

    # Strategy 3: Direct search on Indian financial sites
    for fetcher in [
        lambda: _scrape_et_search(symbol, max_items),
        lambda: _scrape_moneycontrol_search(symbol, max_items),
        lambda: _scrape_livemint_search(symbol, max_items),
    ]:
        try:
            results = fetcher()
            if results:
                return results
        except Exception:
            pass

    return []


def analyze_sentiment(news_items: list[dict]) -> dict:
    """
    Run FinBERT sentiment analysis on news items.
    Input: list of {"headline": str, "url": str}
    Returns: {"label": "positive/neutral/negative", "score": 0.0-1.0, "details": [...]}
    """
    if not news_items:
        return {"label": "neutral", "score": 0.5, "details": []}

    pipe = _get_pipeline()
    details = []
    scores = {"positive": 0, "neutral": 0, "negative": 0}

    for item in news_items:
        headline = item.get("headline", "") if isinstance(item, dict) else str(item)
        url = item.get("url", "") if isinstance(item, dict) else ""
        try:
            result = pipe(headline[:512])  # Truncate long headlines
            if result and isinstance(result[0], list):
                result = result[0]

            best = max(result, key=lambda x: x["score"])
            label = best["label"].lower()
            details.append({
                "headline": headline,
                "url": url,
                "label": label,
                "score": best["score"],
            })
            scores[label] = scores.get(label, 0) + best["score"]
        except Exception:
            details.append({
                "headline": headline,
                "url": url,
                "label": "neutral",
                "score": 0.5,
            })
            scores["neutral"] += 0.5

    # Determine dominant sentiment
    dominant = max(scores, key=scores.get)
    total = sum(scores.values())
    confidence = scores[dominant] / total if total > 0 else 0.5

    return {
        "label": dominant,
        "score": round(confidence, 3),
        "details": details,
    }


def get_stock_sentiment(symbol: str) -> dict:
    """Fetch news and analyze sentiment for a stock."""
    news_items = fetch_news_headlines(symbol)
    if not news_items:
        return {
            "label": "neutral",
            "score": 0.5,
            "details": [],
            "headlines_found": 0,
            "source": "no_news",
        }

    result = analyze_sentiment(news_items)
    result["headlines_found"] = len(news_items)
    result["source"] = "finbert"
    return result

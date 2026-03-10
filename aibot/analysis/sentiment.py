"""News sentiment analysis using FinBERT with multi-source headline fetching."""

import time
import threading
import requests
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from config import FINBERT_MODEL, MAX_NEWS_HEADLINES

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


def _fetch_google_news_rss(query: str, max_items: int) -> list[str]:
    """Fetch headlines from Google News RSS."""
    url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        session = _get_session()
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "xml")
        items = soup.find_all("item", limit=max_items)
        headlines = [item.title.text.strip() for item in items if item.title]
        return headlines
    except Exception:
        return []


def _fetch_bing_news_rss(query: str, max_items: int) -> list[str]:
    """Fetch headlines from Bing News RSS (fallback)."""
    url = f"https://www.bing.com/news/search?q={quote_plus(query)}&format=rss"
    try:
        session = _get_session()
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "xml")
        items = soup.find_all("item", limit=max_items)
        headlines = [item.title.text.strip() for item in items if item.title]
        return headlines
    except Exception:
        return []


def fetch_news_headlines(symbol: str, max_items: int = MAX_NEWS_HEADLINES) -> list[str]:
    """
    Fetch recent news headlines for an NSE stock.
    Uses multiple search strategies with fallback:
    1. Google News RSS with symbol + context
    2. Google News RSS with just symbol
    3. Bing News RSS as fallback
    Returns list of headline strings.
    """
    headlines = []

    # Strategy 1: Google News with NSE context
    search_queries = [
        f"{symbol} NSE share price",
        f"{symbol} stock India",
    ]

    for query in search_queries:
        headlines = _fetch_google_news_rss(query, max_items)
        if headlines:
            return headlines
        time.sleep(0.3)  # Brief pause between attempts

    # Strategy 2: Bing News fallback
    for query in [f"{symbol} NSE stock", f"{symbol} share price India"]:
        headlines = _fetch_bing_news_rss(query, max_items)
        if headlines:
            return headlines
        time.sleep(0.3)

    return []


def analyze_sentiment(headlines: list[str]) -> dict:
    """
    Run FinBERT sentiment analysis on headlines.
    Returns: {"label": "positive/neutral/negative", "score": 0.0-1.0, "details": [...]}
    """
    if not headlines:
        return {"label": "neutral", "score": 0.5, "details": []}

    pipe = _get_pipeline()
    details = []
    scores = {"positive": 0, "neutral": 0, "negative": 0}

    for headline in headlines:
        try:
            result = pipe(headline[:512])  # Truncate long headlines
            if result and isinstance(result[0], list):
                result = result[0]

            best = max(result, key=lambda x: x["score"])
            label = best["label"].lower()
            details.append({"headline": headline, "label": label, "score": best["score"]})
            scores[label] = scores.get(label, 0) + best["score"]
        except Exception:
            details.append({"headline": headline, "label": "neutral", "score": 0.5})
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
    headlines = fetch_news_headlines(symbol)
    if not headlines:
        return {
            "label": "neutral",
            "score": 0.5,
            "details": [],
            "headlines_found": 0,
            "source": "no_news",
        }

    result = analyze_sentiment(headlines)
    result["headlines_found"] = len(headlines)
    result["source"] = "finbert"
    return result

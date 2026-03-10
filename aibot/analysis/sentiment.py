"""News sentiment analysis using FinBERT."""

import requests
from bs4 import BeautifulSoup
from config import FINBERT_MODEL, MAX_NEWS_HEADLINES

# Lazy-load the pipeline to avoid slow imports at startup
_sentiment_pipeline = None


def _get_pipeline():
    """Lazy-load FinBERT sentiment pipeline."""
    global _sentiment_pipeline
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


def fetch_news_headlines(symbol: str, max_items: int = MAX_NEWS_HEADLINES) -> list[str]:
    """
    Fetch recent news headlines for an NSE stock via Google News RSS.
    Returns list of headline strings.
    """
    query = f"{symbol} NSE stock"
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "xml")
        items = soup.find_all("item", limit=max_items)
        headlines = [item.title.text.strip() for item in items if item.title]
        return headlines
    except Exception as e:
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
        return {"label": "neutral", "score": 0.5, "details": [], "headlines_found": 0}

    result = analyze_sentiment(headlines)
    result["headlines_found"] = len(headlines)
    return result

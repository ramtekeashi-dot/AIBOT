"""Composite Swing Score calculator and stock ranking."""

from config import WEIGHTS, TOP_N
from aibot.scoring.normalizer import (
    normalize_trend,
    normalize_volume,
    normalize_momentum,
    normalize_atr,
    normalize_delivery,
    normalize_sentiment,
    normalize_sector_momentum,
)
from aibot.scoring.filters import apply_filters


def compute_swing_score(stock_data: dict, all_sector_returns: list[float]) -> dict:
    """
    Compute weighted composite Swing Score (0-100) for a single stock.

    stock_data must contain:
        - trend: {pct_5d, pct_10d, pct_20d, ema_aligned}
        - rsi: float
        - macd: {status: str}
        - atr_pct: float
        - volume_expansion: float
        - delivery_pct: float
        - sentiment: {label: str, score: float}
        - sector_momentum: float

    Returns enriched stock_data dict with 'swing_score' and 'normalized_scores'.
    """
    trend = stock_data.get("trend", {})
    norm = {
        "trend": normalize_trend(
            trend.get("pct_5d", 0),
            trend.get("pct_10d", 0),
            trend.get("pct_20d", 0),
            trend.get("ema_aligned", False),
        ),
        "volume": normalize_volume(stock_data.get("volume_expansion", 1.0)),
        "momentum": normalize_momentum(
            stock_data.get("rsi", 50),
            stock_data.get("macd", {}).get("status", "neutral"),
        ),
        "volatility": normalize_atr(stock_data.get("atr_pct", 0)),
        "delivery": normalize_delivery(stock_data.get("delivery_pct", 50)),
        "sentiment": normalize_sentiment(
            stock_data.get("sentiment", {}).get("label", "neutral"),
            stock_data.get("sentiment", {}).get("score", 0.5),
        ),
        "sector": normalize_sector_momentum(
            stock_data.get("sector_momentum", 0),
            all_sector_returns,
        ),
    }

    # Weighted composite score
    score = sum(norm[k] * WEIGHTS[k] for k in WEIGHTS)
    score = round(min(max(score, 0), 100), 2)

    stock_data["normalized_scores"] = norm
    stock_data["swing_score"] = score
    return stock_data


def rank_and_select(
    stocks: list[dict],
    category: str,
    all_sector_returns: list[float],
    top_n: int = TOP_N,
) -> list[dict]:
    """
    Filter, score, rank, and select top N stocks from a category.

    Args:
        stocks: list of stock_data dicts (with all indicators computed)
        category: 'midcap' or 'smallcap'
        all_sector_returns: list of all sector returns for normalization
        top_n: number of top picks to return

    Returns: sorted list of top_n stock dicts with swing_score.
    """
    scored = []
    filtered_out = 0

    for stock in stocks:
        # Apply hard filters
        passed, reason = apply_filters(stock)
        if not passed:
            stock["filter_status"] = reason
            filtered_out += 1
            continue

        # Compute swing score
        stock = compute_swing_score(stock, all_sector_returns)
        stock["category"] = category
        stock["filter_status"] = "Passed"
        scored.append(stock)

    print(f"[INFO] {category.upper()}: {len(scored)} passed filters, {filtered_out} excluded.")

    # Sort by swing score descending
    scored.sort(key=lambda x: x["swing_score"], reverse=True)

    return scored[:top_n]

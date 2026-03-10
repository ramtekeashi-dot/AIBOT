"""Normalize technical indicators to 0-100 scale for composite scoring."""

import numpy as np


def normalize_trend(pct_5d: float, pct_10d: float, pct_20d: float, ema_aligned: bool) -> float:
    """
    Normalize trend strength to 0-100.
    Combines short/medium/long price changes + EMA alignment bonus.
    """
    # Weighted average of price changes (recent weighted more)
    weighted_pct = pct_5d * 0.5 + pct_10d * 0.3 + pct_20d * 0.2

    # Map to 0-100: -10% → 0, 0% → 50, +10% → 100
    score = np.clip((weighted_pct + 10) / 20 * 100, 0, 100)

    # EMA alignment bonus (+10 points, capped at 100)
    if ema_aligned:
        score = min(score + 10, 100)

    return round(float(score), 2)


def normalize_volume(expansion_ratio: float) -> float:
    """
    Normalize volume expansion to 0-100.
    0.5x → 0, 1.0x → 40, 1.5x → 70, 2.0x+ → 100.
    """
    if expansion_ratio <= 0.5:
        return 0.0
    if expansion_ratio >= 2.0:
        return 100.0
    # Linear interpolation from 0.5→0 to 2.0→100
    score = (expansion_ratio - 0.5) / 1.5 * 100
    return round(float(np.clip(score, 0, 100)), 2)


def normalize_rsi(rsi: float) -> float:
    """
    Normalize RSI to 0-100 for swing trading.
    Sweet spot: 40-60 (highest score). Tapers towards extremes.
    30-40 and 60-70 still good. Below 30 or above 70 penalized.
    """
    if 40 <= rsi <= 60:
        return 100.0
    elif 30 <= rsi < 40:
        return 60 + (rsi - 30) * 4  # 60→100
    elif 60 < rsi <= 70:
        return 100 - (rsi - 60) * 4  # 100→60
    elif 25 <= rsi < 30:
        return 40 + (rsi - 25) * 4  # 40→60
    elif 70 < rsi <= 75:
        return 60 - (rsi - 70) * 8  # 60→20
    elif rsi < 25:
        return max(0, rsi * 1.6)  # 0→40
    else:
        return max(0, 100 - (rsi - 50) * 2)  # Fallback


def normalize_macd(status: str) -> float:
    """
    Normalize MACD status to 0-100.
    bullish_crossover=100, bullish=75, neutral=50, bearish=25, bearish_crossover=0.
    """
    mapping = {
        "bullish_crossover": 100.0,
        "bullish": 75.0,
        "neutral": 50.0,
        "bearish": 25.0,
        "bearish_crossover": 0.0,
    }
    return mapping.get(status, 50.0)


def normalize_momentum(rsi: float, macd_status: str) -> float:
    """Combined momentum score from RSI + MACD (equal weight)."""
    rsi_score = normalize_rsi(rsi)
    macd_score = normalize_macd(macd_status)
    return round((rsi_score + macd_score) / 2, 2)


def normalize_atr(atr_pct: float) -> float:
    """
    Normalize ATR% for swing trading suitability.
    Sweet spot: 1.5-3.5% (highest score). Too low = no movement, too high = risky.
    """
    if 1.5 <= atr_pct <= 3.5:
        return 100.0
    elif atr_pct < 1.5:
        # Below sweet spot: 0% → 20, 1.5% → 100
        return max(20, atr_pct / 1.5 * 100)
    else:
        # Above sweet spot: 3.5% → 100, 6% → 0
        score = max(0, 100 - (atr_pct - 3.5) / 2.5 * 100)
        return round(float(score), 2)


def normalize_delivery(delivery_pct: float) -> float:
    """
    Normalize delivery % to 0-100. Higher delivery = stronger conviction.
    10% → 0, 50% → 57, 80%+ → 100.
    """
    if delivery_pct <= 10:
        return 0.0
    if delivery_pct >= 80:
        return 100.0
    return round((delivery_pct - 10) / 70 * 100, 2)


def normalize_sentiment(label: str, confidence: float = 0.5) -> float:
    """
    Normalize sentiment to 0-100.
    positive → 70-100 (scaled by confidence), neutral → 50, negative → 0-30.
    """
    if label == "positive":
        return round(70 + confidence * 30, 2)
    elif label == "negative":
        return round(30 - confidence * 30, 2)
    else:
        return 50.0


def normalize_sector_momentum(sector_return: float, all_sector_returns: list[float]) -> float:
    """
    Normalize sector momentum using min-max across all sectors.
    """
    if not all_sector_returns or len(all_sector_returns) < 2:
        return 50.0

    min_r = min(all_sector_returns)
    max_r = max(all_sector_returns)

    if max_r == min_r:
        return 50.0

    score = (sector_return - min_r) / (max_r - min_r) * 100
    return round(float(np.clip(score, 0, 100)), 2)

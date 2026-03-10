"""Support and Resistance level calculation."""

import pandas as pd
import numpy as np
from scipy.signal import find_peaks


def calculate_pivot_points(high: float, low: float, close: float) -> dict:
    """
    Calculate standard pivot points.
    Returns: pivot, S1, S2, R1, R2.
    """
    pivot = (high + low + close) / 3
    r1 = 2 * pivot - low
    r2 = pivot + (high - low)
    s1 = 2 * pivot - high
    s2 = pivot - (high - low)

    return {
        "pivot": round(pivot, 2),
        "r1": round(r1, 2),
        "r2": round(r2, 2),
        "s1": round(s1, 2),
        "s2": round(s2, 2),
    }


def find_swing_levels(df: pd.DataFrame, lookback: int = 60) -> dict:
    """
    Find support and resistance levels using local peaks/valleys.
    Uses scipy.signal.find_peaks on recent data.

    Returns: {support: float, resistance: float, pivot_points: dict}
    """
    if df is None or len(df) < 10:
        return {"support": 0, "resistance": 0, "pivot_points": {}}

    # Use last N days
    recent = df.tail(lookback)
    close = recent["Close"].values.astype(float)
    current_price = close[-1]

    # Find resistance levels (peaks)
    peaks, _ = find_peaks(close, distance=5, prominence=current_price * 0.01)
    # Find support levels (valleys)
    valleys, _ = find_peaks(-close, distance=5, prominence=current_price * 0.01)

    # Get nearest support below current price
    support_levels = close[valleys] if len(valleys) > 0 else np.array([])
    support_below = support_levels[support_levels < current_price]
    support = float(support_below.max()) if len(support_below) > 0 else round(current_price * 0.95, 2)

    # Get nearest resistance above current price
    resistance_levels = close[peaks] if len(peaks) > 0 else np.array([])
    resistance_above = resistance_levels[resistance_levels > current_price]
    resistance = float(resistance_above.min()) if len(resistance_above) > 0 else round(current_price * 1.05, 2)

    # Also compute pivot points from last session
    last_high = float(recent["High"].iloc[-1])
    last_low = float(recent["Low"].iloc[-1])
    last_close = float(recent["Close"].iloc[-1])
    pivots = calculate_pivot_points(last_high, last_low, last_close)

    return {
        "support": round(support, 2),
        "resistance": round(resistance, 2),
        "pivot_points": pivots,
    }

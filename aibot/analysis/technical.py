"""Technical analysis indicators: RSI, MACD, ATR, EMA trends, volume expansion."""

import pandas as pd
import pandas_ta as ta
import numpy as np
from config import (
    RSI_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL, ATR_PERIOD,
    TREND_5D, TREND_10D, TREND_20D, VOLUME_SHORT, VOLUME_LONG,
)


def compute_rsi(df: pd.DataFrame, period: int = RSI_PERIOD) -> float:
    """Compute RSI (14-period) from OHLCV DataFrame. Returns latest RSI value."""
    rsi = ta.rsi(df["Close"], length=period)
    if rsi is None or rsi.dropna().empty:
        return 50.0
    return round(float(rsi.dropna().iloc[-1]), 2)


def compute_macd(df: pd.DataFrame) -> dict:
    """
    Compute MACD indicator.
    Returns dict with keys: macd, signal, histogram, status.
    status: 'bullish_crossover', 'bearish_crossover', 'bullish', 'bearish', 'neutral'
    """
    macd_df = ta.macd(df["Close"], fast=MACD_FAST, slow=MACD_SLOW, signal=MACD_SIGNAL)
    if macd_df is None or macd_df.dropna().empty:
        return {"macd": 0, "signal": 0, "histogram": 0, "status": "neutral"}

    macd_col = [c for c in macd_df.columns if "MACD_" in c and "s" not in c.lower() and "h" not in c.lower()]
    signal_col = [c for c in macd_df.columns if "MACDs_" in c]
    hist_col = [c for c in macd_df.columns if "MACDh_" in c]

    macd_val = float(macd_df[macd_col[0]].dropna().iloc[-1]) if macd_col else 0
    signal_val = float(macd_df[signal_col[0]].dropna().iloc[-1]) if signal_col else 0
    hist_val = float(macd_df[hist_col[0]].dropna().iloc[-1]) if hist_col else 0

    # Determine crossover status
    if hist_col and len(macd_df[hist_col[0]].dropna()) >= 2:
        hist_series = macd_df[hist_col[0]].dropna()
        prev_hist = float(hist_series.iloc[-2])
        curr_hist = hist_val

        if prev_hist < 0 and curr_hist > 0:
            status = "bullish_crossover"
        elif prev_hist > 0 and curr_hist < 0:
            status = "bearish_crossover"
        elif curr_hist > 0:
            status = "bullish"
        elif curr_hist < 0:
            status = "bearish"
        else:
            status = "neutral"
    else:
        status = "bullish" if hist_val > 0 else ("bearish" if hist_val < 0 else "neutral")

    return {
        "macd": round(macd_val, 2),
        "signal": round(signal_val, 2),
        "histogram": round(hist_val, 2),
        "status": status,
    }


def compute_atr_pct(df: pd.DataFrame, period: int = ATR_PERIOD) -> float:
    """Compute ATR as percentage of current price."""
    atr = ta.atr(df["High"], df["Low"], df["Close"], length=period)
    if atr is None or atr.dropna().empty:
        return 0.0
    atr_val = float(atr.dropna().iloc[-1])
    price = float(df["Close"].iloc[-1])
    if price == 0:
        return 0.0
    return round((atr_val / price) * 100, 2)


def compute_trend_strength(df: pd.DataFrame) -> dict:
    """
    Compute trend strength based on price changes and EMA alignment.
    Returns dict with price changes and EMA alignment status.
    """
    close = df["Close"]
    n = len(close)

    # Price changes
    pct_5d = _pct_change(close, TREND_5D) if n > TREND_5D else 0
    pct_10d = _pct_change(close, TREND_10D) if n > TREND_10D else 0
    pct_20d = _pct_change(close, TREND_20D) if n > TREND_20D else 0

    # EMA alignment
    ema5 = ta.ema(close, length=5)
    ema10 = ta.ema(close, length=10)
    ema20 = ta.ema(close, length=20)

    ema_aligned = False
    if ema5 is not None and ema10 is not None and ema20 is not None:
        e5 = float(ema5.dropna().iloc[-1]) if not ema5.dropna().empty else 0
        e10 = float(ema10.dropna().iloc[-1]) if not ema10.dropna().empty else 0
        e20 = float(ema20.dropna().iloc[-1]) if not ema20.dropna().empty else 0
        ema_aligned = e5 > e10 > e20

    return {
        "pct_5d": round(pct_5d, 2),
        "pct_10d": round(pct_10d, 2),
        "pct_20d": round(pct_20d, 2),
        "ema_aligned": ema_aligned,
    }


def compute_volume_expansion(df: pd.DataFrame) -> float:
    """
    Compute volume expansion ratio: 5D avg volume / 20D avg volume.
    Returns ratio (1.0 = no expansion, >1.0 = expansion).
    """
    vol = df["Volume"]
    if len(vol) < VOLUME_LONG:
        return 1.0

    avg_short = vol.tail(VOLUME_SHORT).mean()
    avg_long = vol.tail(VOLUME_LONG).mean()

    if avg_long == 0:
        return 1.0
    return round(float(avg_short / avg_long), 2)


def compute_all_technicals(df: pd.DataFrame) -> dict:
    """Compute all technical indicators for a single stock."""
    price = float(df["Close"].iloc[-1])
    trend = compute_trend_strength(df)
    rsi = compute_rsi(df)
    macd = compute_macd(df)
    atr_pct = compute_atr_pct(df)
    vol_expansion = compute_volume_expansion(df)

    return {
        "price": round(price, 2),
        "trend": trend,
        "rsi": rsi,
        "macd": macd,
        "atr_pct": atr_pct,
        "volume_expansion": vol_expansion,
    }


def _pct_change(series: pd.Series, periods: int) -> float:
    """Calculate percentage change over N periods."""
    if len(series) <= periods:
        return 0.0
    old = float(series.iloc[-periods - 1])
    new = float(series.iloc[-1])
    if old == 0:
        return 0.0
    return ((new - old) / old) * 100

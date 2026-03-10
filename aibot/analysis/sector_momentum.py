"""Sector momentum analysis — compute sector-level 10D returns."""

import pandas as pd
import numpy as np
from config import SECTOR_LOOKBACK, SECTOR_FALLBACK


def get_sector_for_symbol(symbol: str, sector_cache: dict = None) -> str:
    """Get sector for a given NSE symbol."""
    # Check cache first
    if sector_cache and symbol in sector_cache:
        return sector_cache[symbol]

    # Check fallback mapping
    for sector, symbols in SECTOR_FALLBACK.items():
        if symbol in symbols:
            return sector

    # Try yfinance (expensive, use sparingly)
    try:
        import yfinance as yf
        info = yf.Ticker(f"{symbol}.NS").info
        sector = info.get("sector", "Unknown")
        if sector_cache is not None:
            sector_cache[symbol] = sector
        return sector
    except Exception:
        return "Unknown"


def compute_sector_returns(
    ohlcv_data: dict[str, pd.DataFrame],
    sector_cache: dict = None,
    lookback: int = SECTOR_LOOKBACK,
) -> dict[str, float]:
    """
    Compute average N-day return for each sector.
    Returns dict: sector_name → avg_return_pct.
    """
    sector_returns = {}  # sector → list of returns

    for symbol, df in ohlcv_data.items():
        if len(df) < lookback + 1:
            continue

        sector = get_sector_for_symbol(symbol, sector_cache)
        close = df["Close"]
        ret = ((float(close.iloc[-1]) - float(close.iloc[-lookback - 1])) / float(close.iloc[-lookback - 1])) * 100

        if sector not in sector_returns:
            sector_returns[sector] = []
        sector_returns[sector].append(ret)

    # Average per sector
    result = {}
    for sector, returns in sector_returns.items():
        result[sector] = round(np.mean(returns), 2)

    return result


def get_stock_sector_momentum(
    symbol: str,
    sector_returns: dict[str, float],
    sector_cache: dict = None,
) -> float:
    """Get sector momentum for a specific stock. Returns sector 10D return %."""
    sector = get_sector_for_symbol(symbol, sector_cache)
    return sector_returns.get(sector, 0.0)

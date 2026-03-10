"""Fetch OHLCV price data via yfinance."""

import yfinance as yf
import pandas as pd
from config import OHLCV_PERIOD


def fetch_ohlcv(symbols: list[str], period: str = OHLCV_PERIOD) -> dict[str, pd.DataFrame]:
    """
    Batch download OHLCV data for all symbols.
    Returns dict mapping symbol → DataFrame with columns [Open, High, Low, Close, Volume].
    """
    if not symbols:
        return {}

    yf_symbols = [s if s.endswith(".NS") else f"{s}.NS" for s in symbols]
    print(f"[INFO] Downloading OHLCV data for {len(yf_symbols)} stocks...")

    try:
        data = yf.download(
            tickers=yf_symbols,
            period=period,
            group_by="ticker",
            threads=True,
            progress=False,
        )
    except Exception as e:
        print(f"[ERROR] Batch download failed: {e}")
        return {}

    result = {}
    for sym in yf_symbols:
        base = sym.replace(".NS", "")
        try:
            if len(yf_symbols) == 1:
                df = data.copy()
            else:
                df = data[sym].copy()

            df = df.dropna(subset=["Close"])
            if len(df) >= 5:
                result[base] = df
        except (KeyError, TypeError):
            continue

    print(f"[INFO] Got valid OHLCV data for {len(result)}/{len(yf_symbols)} stocks.")
    return result


def get_current_price(df: pd.DataFrame) -> float:
    """Get the latest closing price from OHLCV DataFrame."""
    if df is None or df.empty:
        return 0.0
    return float(df["Close"].iloc[-1])

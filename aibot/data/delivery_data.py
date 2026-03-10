"""Fetch delivery percentage data from NSE."""

import requests
import pandas as pd


def fetch_delivery_pct(symbol: str) -> float:
    """
    Fetch recent average delivery % for an NSE stock.
    Returns delivery percentage (0-100) or 50.0 as default fallback.
    """
    try:
        return _fetch_from_nse_api(symbol)
    except Exception:
        pass

    return 50.0  # Default fallback


def _fetch_from_nse_api(symbol: str) -> float:
    """Fetch delivery data from NSE India equity info API."""
    url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}&section=trade_info"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }

    session = requests.Session()
    # First hit main page to get cookies
    session.get("https://www.nseindia.com", headers=headers, timeout=10)

    resp = session.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    # Extract delivery percentage from security-wise delivery data
    if "securityWiseDP" in data:
        dp = data["securityWiseDP"]
        if "deliveryQuantity" in dp and "tradedQuantity" in dp:
            traded = float(dp["tradedQuantity"].replace(",", ""))
            delivered = float(dp["deliveryQuantity"].replace(",", ""))
            if traded > 0:
                return round((delivered / traded) * 100, 2)

    # Try marketDeptOrderBook
    if "marketDeptOrderBook" in data:
        trade_info = data["marketDeptOrderBook"].get("tradeInfo", {})
        if "deliveryToTradedQuantity" in trade_info:
            return float(trade_info["deliveryToTradedQuantity"])

    return 50.0


def fetch_delivery_batch(symbols: list[str]) -> dict[str, float]:
    """Fetch delivery % for multiple symbols. Returns dict symbol → delivery_pct."""
    result = {}
    for sym in symbols:
        result[sym] = fetch_delivery_pct(sym)
    return result

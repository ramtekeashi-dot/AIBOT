"""Fetch FII/DII institutional activity data from NSE."""

import requests
import pandas as pd
from datetime import datetime


def fetch_fii_dii_activity() -> dict:
    """
    Fetch latest FII/DII cash market activity from NSE.
    Returns dict with keys: fii_net, dii_net, fii_buy, fii_sell, dii_buy, dii_sell.
    Values in INR crores.
    """
    try:
        return _fetch_from_nse()
    except Exception as e:
        print(f"[WARN] FII/DII data unavailable: {e}")
        return {"fii_net": 0, "dii_net": 0, "fii_buy": 0, "fii_sell": 0, "dii_buy": 0, "dii_sell": 0}


def _fetch_from_nse() -> dict:
    """Fetch FII/DII data from NSE India API."""
    url = "https://www.nseindia.com/api/fiidiiTradeReact"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers, timeout=10)

    resp = session.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    result = {"fii_net": 0, "dii_net": 0, "fii_buy": 0, "fii_sell": 0, "dii_buy": 0, "dii_sell": 0}

    for entry in data:
        category = entry.get("category", "").upper()
        if "FII" in category or "FPI" in category:
            result["fii_buy"] = _parse_amount(entry.get("buyValue", "0"))
            result["fii_sell"] = _parse_amount(entry.get("sellValue", "0"))
            result["fii_net"] = result["fii_buy"] - result["fii_sell"]
        elif "DII" in category:
            result["dii_buy"] = _parse_amount(entry.get("buyValue", "0"))
            result["dii_sell"] = _parse_amount(entry.get("sellValue", "0"))
            result["dii_net"] = result["dii_buy"] - result["dii_sell"]

    return result


def _parse_amount(value) -> float:
    """Parse amount string to float."""
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return 0.0


def get_institutional_bias() -> str:
    """Return overall institutional bias: bullish, bearish, or neutral."""
    data = fetch_fii_dii_activity()
    net = data["fii_net"] + data["dii_net"]
    if net > 500:
        return "bullish"
    elif net < -500:
        return "bearish"
    return "neutral"

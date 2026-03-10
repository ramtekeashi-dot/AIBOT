"""Fetch Nifty Midcap 150 and Nifty Smallcap 250 constituent lists."""

import requests
import pandas as pd


def _fetch_niftyindices_csv(index_name: str) -> list[str]:
    """Download constituent CSV from niftyindices.com."""
    url = f"https://www.niftyindices.com/IndexConstituent/{index_name}.csv"
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        from io import StringIO
        df = pd.read_csv(StringIO(resp.text))
        col = [c for c in df.columns if "symbol" in c.lower()]
        if col:
            return df[col[0]].str.strip().tolist()
    except Exception:
        pass
    return []


def get_midcap150() -> list[str]:
    """Return list of Nifty Midcap 150 NSE symbols."""
    try:
        from niftystocks import ns
        symbols = ns.get_nifty_midcap150()
        if symbols:
            return [s.replace(".NS", "") for s in symbols]
    except Exception:
        pass

    # Fallback: niftyindices CSV
    symbols = _fetch_niftyindices_csv("Nifty Midcap 150")
    if symbols:
        return symbols

    print("[WARN] Could not fetch Midcap 150 constituents, using fallback sample.")
    return _fallback_midcap()


def get_smallcap250() -> list[str]:
    """Return list of Nifty Smallcap 250 NSE symbols."""
    try:
        from niftystocks import ns
        symbols = ns.get_nifty_smallcap250()
        if symbols:
            return [s.replace(".NS", "") for s in symbols]
    except Exception:
        pass

    symbols = _fetch_niftyindices_csv("Nifty Smallcap 250")
    if symbols:
        return symbols

    print("[WARN] Could not fetch Smallcap 250 constituents, using fallback sample.")
    return _fallback_smallcap()


def to_yfinance_symbols(symbols: list[str]) -> list[str]:
    """Append .NS suffix for yfinance compatibility."""
    return [f"{s}.NS" for s in symbols]


def _fallback_midcap() -> list[str]:
    """Hardcoded sample of Midcap 150 stocks as fallback."""
    return [
        "VOLTAS", "FEDERALBNK", "OBEROIRLTY", "PERSISTENT", "COFORGE",
        "MPHASIS", "GODREJPROP", "AUROPHARMA", "CUMMINSIND", "PIIND",
        "POLYCAB", "ASTRAL", "SUNDARMFIN", "PAGEIND", "TRENT",
        "INDIANHOTELS", "CONCOR", "LAURUSLABS", "BALKRISIND", "PHOENIXLTD",
        "METROPOLIS", "ATUL", "ALKEM", "DEEPAKNTR", "CROMPTON",
        "IPCALAB", "ENDURANCE", "AFFLE", "KPITTECH", "SONACOMS",
        "JUBLFOOD", "LICHSGFIN", "ESCORTS", "BEL", "BHEL",
        "NHPC", "IRCTC", "TATACHEM", "NATIONALUM", "SAIL",
        "PEL", "SUPREMEIND", "THERMAX", "GRINDWELL", "APLAPOLLO",
        "BRIGADE", "FORTIS", "GLAXO", "HONAUT", "RAJESHEXPO",
    ]


def _fallback_smallcap() -> list[str]:
    """Hardcoded sample of Smallcap 250 stocks as fallback."""
    return [
        "ROUTE", "HAPPSTMNDS", "DATAPATTNS", "FINEORG", "CLEAN",
        "KALYANKJIL", "CAMPUS", "MEDANTA", "RAINBOW", "KAYNES",
        "CDSL", "IIFL", "CAMS", "KFINTECH", "ZENTEC",
        "RATNAMANI", "GRSE", "COCHINSHIP", "MAZAGON", "GARDENREACH",
        "TIINDIA", "GPIL", "SPARC", "GRANULES", "LAXMIMACH",
        "NUVAMA", "DOMS", "JYOTHYLAB", "BIKAJI", "DEVYANI",
        "SAPPHIRE", "KIMS", "RHIM", "RITES", "IRCON",
        "RVNL", "HUDCO", "RECLTD", "PFC", "SJVN",
        "JSWINFRA", "NIACL", "STARHEALTH", "ZEEL", "NETWORK18",
        "POWERINDIA", "BLUESTARCO", "GESHIP", "MAZDOCK", "EIDPARRY",
    ]

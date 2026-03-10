"""Report generation — CLI output and CSV export."""

import pandas as pd
from tabulate import tabulate
from datetime import datetime


def generate_report(midcap_top5: list[dict], smallcap_top5: list[dict]) -> str:
    """Generate formatted CLI report for top picks."""
    lines = []
    lines.append("=" * 80)
    lines.append("  AIBOT - SWING TRADING PICKS")
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)

    lines.append("\n" + "─" * 80)
    lines.append("  TOP 5 MIDCAP STOCKS (Nifty Midcap 150)")
    lines.append("─" * 80)
    for i, stock in enumerate(midcap_top5, 1):
        lines.append(_format_stock(i, stock))

    lines.append("\n" + "─" * 80)
    lines.append("  TOP 5 SMALLCAP STOCKS (Nifty Smallcap 250)")
    lines.append("─" * 80)
    for i, stock in enumerate(smallcap_top5, 1):
        lines.append(_format_stock(i, stock))

    lines.append("\n" + "=" * 80)
    return "\n".join(lines)


def _format_stock(rank: int, stock: dict) -> str:
    """Format a single stock entry for CLI output."""
    symbol = stock.get("symbol", "N/A")
    score = stock.get("swing_score", 0)
    price = stock.get("price", 0)
    trend = stock.get("trend", {})
    rsi = stock.get("rsi", 0)
    macd = stock.get("macd", {})
    atr_pct = stock.get("atr_pct", 0)
    vol_exp = stock.get("volume_expansion", 1.0)
    sentiment = stock.get("sentiment", {})
    levels = stock.get("levels", {})
    rationale = stock.get("rationale", "")

    vol_exp_pct = round((vol_exp - 1) * 100, 1)
    vol_sign = "+" if vol_exp_pct >= 0 else ""

    lines = []
    lines.append(f"\n  #{rank} {symbol}  |  Swing Score: {score}/100  |  CMP: INR {price}")
    lines.append(f"  {'─' * 50}")
    lines.append(f"  Trend:    5D: {trend.get('pct_5d', 0):+.1f}%  |  10D: {trend.get('pct_10d', 0):+.1f}%  |  20D: {trend.get('pct_20d', 0):+.1f}%  |  EMA Aligned: {'Yes' if trend.get('ema_aligned') else 'No'}")
    lines.append(f"  Volume:   {vol_sign}{vol_exp_pct}% expansion (5D vs 20D)")
    lines.append(f"  RSI:      {rsi}  |  MACD: {macd.get('status', 'N/A')}")
    lines.append(f"  ATR%:     {atr_pct}%")
    lines.append(f"  Delivery: {stock.get('delivery_pct', 'N/A')}%")
    lines.append(f"  Sentiment: {sentiment.get('label', 'N/A')} (confidence: {sentiment.get('score', 0):.2f})")
    lines.append(f"  Support:  {levels.get('support', 'N/A')}  |  Resistance: {levels.get('resistance', 'N/A')}")

    if rationale:
        lines.append(f"  Rationale: {rationale}")

    return "\n".join(lines)


def export_csv(midcap: list[dict], smallcap: list[dict], filename: str = "swing_picks.csv"):
    """Export top picks to CSV."""
    all_stocks = midcap + smallcap
    rows = []

    for stock in all_stocks:
        trend = stock.get("trend", {})
        macd = stock.get("macd", {})
        sentiment = stock.get("sentiment", {})
        levels = stock.get("levels", {})
        norm = stock.get("normalized_scores", {})

        rows.append({
            "Category": stock.get("category", ""),
            "Symbol": stock.get("symbol", ""),
            "Price": stock.get("price", 0),
            "Swing Score": stock.get("swing_score", 0),
            "Trend 5D%": trend.get("pct_5d", 0),
            "Trend 10D%": trend.get("pct_10d", 0),
            "Trend 20D%": trend.get("pct_20d", 0),
            "EMA Aligned": trend.get("ema_aligned", False),
            "Volume Expansion": stock.get("volume_expansion", 1.0),
            "RSI": stock.get("rsi", 0),
            "MACD Status": macd.get("status", ""),
            "ATR%": stock.get("atr_pct", 0),
            "Delivery%": stock.get("delivery_pct", 0),
            "Sentiment": sentiment.get("label", ""),
            "Sentiment Score": sentiment.get("score", 0),
            "Support": levels.get("support", 0),
            "Resistance": levels.get("resistance", 0),
            "Trend Score": norm.get("trend", 0),
            "Volume Score": norm.get("volume", 0),
            "Momentum Score": norm.get("momentum", 0),
            "Volatility Score": norm.get("volatility", 0),
            "Delivery Score": norm.get("delivery", 0),
            "Sentiment Score Norm": norm.get("sentiment", 0),
            "Sector Score": norm.get("sector", 0),
        })

    df = pd.DataFrame(rows)
    df.to_csv(filename, index=False)
    print(f"[INFO] Results exported to {filename}")
    return df


def to_summary_table(stocks: list[dict]) -> str:
    """Generate a compact summary table using tabulate."""
    rows = []
    for s in stocks:
        rows.append({
            "Symbol": s.get("symbol", ""),
            "Score": s.get("swing_score", 0),
            "Price": s.get("price", 0),
            "RSI": s.get("rsi", 0),
            "MACD": s.get("macd", {}).get("status", ""),
            "ATR%": s.get("atr_pct", 0),
            "Vol Exp": f"{s.get('volume_expansion', 1.0):.1f}x",
            "Sentiment": s.get("sentiment", {}).get("label", ""),
        })
    return tabulate(rows, headers="keys", tablefmt="grid", floatfmt=".1f")

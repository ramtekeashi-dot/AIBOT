"""AIBOT - Main pipeline orchestrator for NSE Swing Trading Analysis."""

import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import MAX_WORKERS, TOP_N
from aibot.data.universe import get_midcap150, get_smallcap250
from aibot.data.price_data import fetch_ohlcv, get_current_price
from aibot.data.delivery_data import fetch_delivery_pct
from aibot.data.fii_dii import fetch_fii_dii_activity
from aibot.analysis.technical import compute_all_technicals
from aibot.analysis.sentiment import get_stock_sentiment
from aibot.analysis.sector_momentum import compute_sector_returns, get_stock_sector_momentum
from aibot.scoring.scorer import rank_and_select
from aibot.output.levels import find_swing_levels
from aibot.output.report import generate_report, export_csv


def run_pipeline(skip_sentiment: bool = False):
    """
    Run the full AIBOT analysis pipeline.

    Args:
        skip_sentiment: If True, skip FinBERT sentiment (faster, uses neutral default).

    Returns:
        tuple: (midcap_top5, smallcap_top5, all_analysis_data)
    """
    start = time.time()

    # ─── Step 1: Fetch Universe ───
    print("\n[STEP 1/8] Fetching universe...")
    midcap_symbols = get_midcap150()
    smallcap_symbols = get_smallcap250()
    all_symbols = midcap_symbols + smallcap_symbols
    print(f"  Midcap: {len(midcap_symbols)} | Smallcap: {len(smallcap_symbols)} | Total: {len(all_symbols)}")

    # ─── Step 2: Fetch OHLCV Data ───
    print("\n[STEP 2/8] Downloading OHLCV data...")
    ohlcv_data = fetch_ohlcv(all_symbols)

    # ─── Step 3: Fetch FII/DII ───
    print("\n[STEP 3/8] Fetching FII/DII activity...")
    fii_dii = fetch_fii_dii_activity()
    print(f"  FII Net: {fii_dii['fii_net']:.0f} Cr | DII Net: {fii_dii['dii_net']:.0f} Cr")

    # ─── Step 4: Compute Sector Momentum ───
    print("\n[STEP 4/8] Computing sector momentum...")
    sector_cache = {}
    sector_returns = compute_sector_returns(ohlcv_data, sector_cache)
    all_sector_return_values = list(sector_returns.values())
    print(f"  Sectors tracked: {len(sector_returns)}")

    # ─── Step 5: Compute Technicals + Delivery + Sentiment ───
    print("\n[STEP 5/8] Analyzing stocks (technicals + delivery + sentiment)...")
    all_stocks = {}

    def analyze_stock(symbol: str) -> tuple[str, dict]:
        """Analyze a single stock — runs in thread pool."""
        df = ohlcv_data.get(symbol)
        if df is None or df.empty:
            return symbol, None

        # Technical indicators
        technicals = compute_all_technicals(df)

        # Delivery %
        delivery_pct = fetch_delivery_pct(symbol)

        # Sentiment
        if skip_sentiment:
            sentiment = {"label": "neutral", "score": 0.5, "details": [], "headlines_found": 0}
        else:
            sentiment = get_stock_sentiment(symbol)

        # Sector momentum
        sector_mom = get_stock_sector_momentum(symbol, sector_returns, sector_cache)

        return symbol, {
            "symbol": symbol,
            **technicals,
            "delivery_pct": delivery_pct,
            "sentiment": sentiment,
            "sector_momentum": sector_mom,
            "df": df,  # Keep reference for S/R levels later
        }

    # Run analysis in parallel (I/O-bound tasks)
    symbols_with_data = [s for s in all_symbols if s in ohlcv_data]
    completed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(analyze_stock, sym): sym for sym in symbols_with_data}
        for future in as_completed(futures):
            symbol, result = future.result()
            if result is not None:
                all_stocks[symbol] = result
            completed += 1
            if completed % 50 == 0:
                print(f"  Processed {completed}/{len(symbols_with_data)} stocks...")

    print(f"  Analyzed {len(all_stocks)} stocks successfully.")

    # ─── Step 6: Score and Rank ───
    print("\n[STEP 6/8] Scoring and ranking...")
    midcap_stocks = [all_stocks[s] for s in midcap_symbols if s in all_stocks]
    smallcap_stocks = [all_stocks[s] for s in smallcap_symbols if s in all_stocks]

    midcap_top5 = rank_and_select(midcap_stocks, "midcap", all_sector_return_values, TOP_N)
    smallcap_top5 = rank_and_select(smallcap_stocks, "smallcap", all_sector_return_values, TOP_N)

    # ─── Step 7: Calculate S/R Levels for Top Picks ───
    print("\n[STEP 7/8] Calculating support/resistance levels...")
    for stock in midcap_top5 + smallcap_top5:
        df = stock.pop("df", None)
        if df is not None:
            stock["levels"] = find_swing_levels(df)
        else:
            stock["levels"] = {"support": 0, "resistance": 0, "pivot_points": {}}

    # ─── Step 8: Generate LLM Rationales ───
    print("\n[STEP 8/8] Generating trading rationales...")
    try:
        from aibot.llm.rationale import batch_generate_rationales
        all_top = midcap_top5 + smallcap_top5
        rationales = batch_generate_rationales(all_top)
        for stock in all_top:
            stock["rationale"] = rationales.get(stock["symbol"], _template_rationale(stock))
    except Exception as e:
        print(f"  [WARN] LLM rationale failed ({e}), using template rationale.")
        for stock in midcap_top5 + smallcap_top5:
            stock["rationale"] = _template_rationale(stock)

    # Remove df references from remaining stocks
    for stock_data in all_stocks.values():
        stock_data.pop("df", None)

    elapsed = time.time() - start
    print(f"\n[DONE] Pipeline completed in {elapsed:.1f}s")

    return midcap_top5, smallcap_top5, all_stocks


def _template_rationale(stock: dict) -> str:
    """Fallback rule-based rationale when LLM is unavailable."""
    parts = []
    trend = stock.get("trend", {})
    macd = stock.get("macd", {})

    if trend.get("ema_aligned"):
        parts.append("Strong uptrend with EMA alignment")
    elif trend.get("pct_5d", 0) > 0:
        parts.append("Short-term bullish momentum")
    else:
        parts.append("Consolidating with potential reversal")

    if macd.get("status") == "bullish_crossover":
        parts.append("fresh MACD bullish crossover signals entry")
    elif macd.get("status") == "bullish":
        parts.append("MACD in bullish territory")

    vol = stock.get("volume_expansion", 1.0)
    if vol > 1.3:
        parts.append(f"volume expanding {vol:.1f}x confirms institutional interest")

    return ". ".join(parts) + "."


def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="AIBOT - NSE Swing Trading Analyst")
    parser.add_argument("--skip-sentiment", action="store_true", help="Skip FinBERT sentiment (faster)")
    parser.add_argument("--no-csv", action="store_true", help="Don't export CSV")
    args = parser.parse_args()

    midcap_top5, smallcap_top5, all_data = run_pipeline(skip_sentiment=args.skip_sentiment)

    # Print report
    report = generate_report(midcap_top5, smallcap_top5)
    print(report)

    # Export CSV
    if not args.no_csv:
        export_csv(midcap_top5, smallcap_top5)


if __name__ == "__main__":
    main()

"""Hard filter rules — exclude stocks that fail any filter."""

from config import RSI_MAX, DELIVERY_MIN, ATR_PCT_MAX, PRICE_MIN


def apply_filters(stock_data: dict) -> tuple[bool, str]:
    """
    Apply hard exclusion filters to a stock.
    Returns (passed: bool, reason: str).
    """
    price = stock_data.get("price", 0)
    rsi = stock_data.get("rsi", 50)
    delivery_pct = stock_data.get("delivery_pct", 50)
    atr_pct = stock_data.get("atr_pct", 0)
    sentiment_label = stock_data.get("sentiment", {}).get("label", "neutral")

    if price < PRICE_MIN:
        return False, f"Price {price} < {PRICE_MIN}"

    if rsi > RSI_MAX:
        return False, f"RSI {rsi} > {RSI_MAX} (overbought)"

    if delivery_pct < DELIVERY_MIN:
        return False, f"Delivery {delivery_pct}% < {DELIVERY_MIN}%"

    if atr_pct > ATR_PCT_MAX:
        return False, f"ATR% {atr_pct} > {ATR_PCT_MAX}% (too volatile)"

    if sentiment_label == "negative":
        return False, "Negative news sentiment"

    return True, "Passed"

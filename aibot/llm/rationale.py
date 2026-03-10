"""LLM-powered trading rationale generation using Claude or GPT."""

import os
from dotenv import load_dotenv
from config import LLM_MAX_TOKENS, LLM_TEMPERATURE

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-6")


def _get_client():
    """Get the appropriate LLM client based on provider config."""
    if LLM_PROVIDER == "anthropic":
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key or api_key.startswith("your-"):
            raise ValueError("ANTHROPIC_API_KEY not configured in .env")
        return anthropic.Anthropic(api_key=api_key), "anthropic"
    elif LLM_PROVIDER == "openai":
        import openai
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key or api_key.startswith("your-"):
            raise ValueError("OPENAI_API_KEY not configured in .env")
        return openai.OpenAI(api_key=api_key), "openai"
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")


SYSTEM_PROMPT = """You are an expert swing trading analyst specializing in Indian equities (NSE).
Given stock analysis data, generate a concise 2-3 line trading rationale.
Be specific, actionable, and trader-friendly. No disclaimers. No generic advice.
Focus on: entry logic, key catalysts, and risk/reward setup."""


def generate_rationale(stock_data: dict) -> str:
    """
    Generate a 2-3 line swing trading rationale for a stock using LLM.

    Args:
        stock_data: dict with symbol, swing_score, trend, rsi, macd, atr_pct,
                    sentiment, levels, volume_expansion, delivery_pct, etc.

    Returns: rationale string.
    """
    trend = stock_data.get("trend", {})
    macd = stock_data.get("macd", {})
    sentiment = stock_data.get("sentiment", {})
    levels = stock_data.get("levels", {})
    norm = stock_data.get("normalized_scores", {})

    user_prompt = f"""Stock: {stock_data.get('symbol')}
Price: INR {stock_data.get('price')}
Swing Score: {stock_data.get('swing_score')}/100
Category: {stock_data.get('category', 'N/A')}

Trend: 5D {trend.get('pct_5d', 0):+.1f}%, 10D {trend.get('pct_10d', 0):+.1f}%, 20D {trend.get('pct_20d', 0):+.1f}%
EMA Aligned: {'Yes' if trend.get('ema_aligned') else 'No'}
RSI: {stock_data.get('rsi')}
MACD: {macd.get('status')} (histogram: {macd.get('histogram')})
ATR%: {stock_data.get('atr_pct')}%
Volume Expansion: {stock_data.get('volume_expansion', 1.0):.1f}x
Delivery%: {stock_data.get('delivery_pct')}%
Sentiment: {sentiment.get('label')} (confidence: {sentiment.get('score', 0):.2f})
Support: {levels.get('support')} | Resistance: {levels.get('resistance')}

Component Scores: Trend={norm.get('trend', 0):.0f}, Volume={norm.get('volume', 0):.0f}, Momentum={norm.get('momentum', 0):.0f}, Volatility={norm.get('volatility', 0):.0f}, Delivery={norm.get('delivery', 0):.0f}, Sentiment={norm.get('sentiment', 0):.0f}, Sector={norm.get('sector', 0):.0f}

Generate a 2-3 line swing trading rationale."""

    try:
        client, provider = _get_client()

        if provider == "anthropic":
            response = client.messages.create(
                model=LLM_MODEL,
                max_tokens=LLM_MAX_TOKENS,
                temperature=LLM_TEMPERATURE,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return response.content[0].text.strip()

        elif provider == "openai":
            response = client.chat.completions.create(
                model=LLM_MODEL,
                max_tokens=LLM_MAX_TOKENS,
                temperature=LLM_TEMPERATURE,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content.strip()

    except Exception as e:
        return f"[LLM unavailable: {e}]"


def batch_generate_rationales(stocks: list[dict]) -> dict[str, str]:
    """
    Generate rationales for multiple stocks.
    Returns dict: symbol → rationale string.
    """
    result = {}
    for stock in stocks:
        symbol = stock.get("symbol", "")
        print(f"  Generating rationale for {symbol}...")
        result[symbol] = generate_rationale(stock)
    return result

"""Conversational Q&A interface over analysis results using LLM."""

import os
import json
from dotenv import load_dotenv
from config import LLM_TEMPERATURE

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-6")


def create_chat_context(
    midcap_top5: list[dict],
    smallcap_top5: list[dict],
    all_data: dict = None,
) -> str:
    """
    Build a system prompt with full analysis data as context for the chat LLM.
    """
    context_parts = [
        "You are AIBOT, an AI Trading Analyst specializing in NSE Indian equities and swing trading.",
        "You have access to the following analysis data from today's scan.",
        "Answer questions concisely and analytically. No disclaimers. Be trader-friendly.",
        "",
        "=== TOP 5 MIDCAP PICKS ===",
    ]

    for stock in midcap_top5:
        context_parts.append(_stock_summary(stock))

    context_parts.append("\n=== TOP 5 SMALLCAP PICKS ===")
    for stock in smallcap_top5:
        context_parts.append(_stock_summary(stock))

    if all_data:
        context_parts.append(f"\nTotal stocks analyzed: {len(all_data)}")

    return "\n".join(context_parts)


def _stock_summary(stock: dict) -> str:
    """Create a compact text summary of a stock for LLM context."""
    trend = stock.get("trend", {})
    macd = stock.get("macd", {})
    sentiment = stock.get("sentiment", {})
    levels = stock.get("levels", {})

    return f"""
{stock.get('symbol')} | Score: {stock.get('swing_score')}/100 | Price: {stock.get('price')} | Category: {stock.get('category', '')}
  Trend: 5D={trend.get('pct_5d', 0):+.1f}% 10D={trend.get('pct_10d', 0):+.1f}% 20D={trend.get('pct_20d', 0):+.1f}% EMA={'Aligned' if trend.get('ema_aligned') else 'Not aligned'}
  RSI={stock.get('rsi')} MACD={macd.get('status')} ATR%={stock.get('atr_pct')}% VolExp={stock.get('volume_expansion', 1.0):.1f}x Del%={stock.get('delivery_pct')}%
  Sentiment={sentiment.get('label')} Support={levels.get('support')} Resistance={levels.get('resistance')}
  Rationale: {stock.get('rationale', 'N/A')}"""


def ask_question(
    question: str,
    system_context: str,
    conversation_history: list[dict] = None,
) -> str:
    """
    Send a question to the LLM with analysis context.

    Args:
        question: User's question
        system_context: Built by create_chat_context()
        conversation_history: Previous messages for multi-turn chat

    Returns: LLM response string.
    """
    if conversation_history is None:
        conversation_history = []

    messages = conversation_history + [{"role": "user", "content": question}]

    try:
        if LLM_PROVIDER == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
            response = client.messages.create(
                model=LLM_MODEL,
                max_tokens=1000,
                temperature=LLM_TEMPERATURE,
                system=system_context,
                messages=messages,
            )
            return response.content[0].text.strip()

        elif LLM_PROVIDER == "openai":
            import openai
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
            oai_messages = [{"role": "system", "content": system_context}] + messages
            response = client.chat.completions.create(
                model=LLM_MODEL,
                max_tokens=1000,
                temperature=LLM_TEMPERATURE,
                messages=oai_messages,
            )
            return response.choices[0].message.content.strip()

        else:
            return f"Unknown LLM provider: {LLM_PROVIDER}"

    except Exception as e:
        return f"Error communicating with LLM: {e}"

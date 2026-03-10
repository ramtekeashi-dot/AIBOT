"""AIBOT - Streamlit Dashboard for NSE Swing Trading Analysis."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="AIBOT - Swing Trading Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    st.title("AIBOT - NSE Swing Trading Analyst")
    st.caption(f"Multi-factor scoring system for Midcap & Smallcap stocks | {datetime.now().strftime('%Y-%m-%d')}")

    # ─── Sidebar ───
    with st.sidebar:
        st.header("Controls")

        if st.button("Run Analysis", type="primary", use_container_width=True):
            _run_analysis()

        skip_sentiment = st.checkbox("Skip Sentiment (faster)", value=False)
        st.session_state["skip_sentiment"] = skip_sentiment

        st.divider()
        st.subheader("Scoring Weights")
        from config import WEIGHTS
        w_trend = st.slider("Trend Strength", 0.0, 0.5, WEIGHTS["trend"], 0.05)
        w_volume = st.slider("Volume Expansion", 0.0, 0.5, WEIGHTS["volume"], 0.05)
        w_momentum = st.slider("Momentum (RSI/MACD)", 0.0, 0.5, WEIGHTS["momentum"], 0.05)
        w_volatility = st.slider("Volatility (ATR)", 0.0, 0.3, WEIGHTS["volatility"], 0.05)
        w_delivery = st.slider("Delivery %", 0.0, 0.3, WEIGHTS["delivery"], 0.05)
        w_sentiment = st.slider("Sentiment", 0.0, 0.3, WEIGHTS["sentiment"], 0.05)
        w_sector = st.slider("Sector Momentum", 0.0, 0.2, WEIGHTS["sector"], 0.05)

        total = w_trend + w_volume + w_momentum + w_volatility + w_delivery + w_sentiment + w_sector
        st.metric("Weight Total", f"{total:.2f}", delta=f"{total - 1.0:+.2f}" if abs(total - 1.0) > 0.01 else None)

    # ─── Main Content ───
    if "midcap_top5" not in st.session_state:
        st.info("Click **Run Analysis** in the sidebar to start the swing trading scan.")
        _show_instructions()
        return

    midcap = st.session_state["midcap_top5"]
    smallcap = st.session_state["smallcap_top5"]

    # Tabs
    tab1, tab2, tab3 = st.tabs(["Scoreboard", "Stock Detail", "Chat with AIBOT"])

    with tab1:
        _render_scoreboard(midcap, smallcap)

    with tab2:
        _render_detail_view(midcap, smallcap)

    with tab3:
        _render_chat()


def _run_analysis():
    """Execute the analysis pipeline."""
    with st.spinner("Running AIBOT analysis pipeline... This may take a few minutes."):
        try:
            from main import run_pipeline
            skip = st.session_state.get("skip_sentiment", False)
            midcap, smallcap, all_data = run_pipeline(skip_sentiment=skip)

            st.session_state["midcap_top5"] = midcap
            st.session_state["smallcap_top5"] = smallcap
            st.session_state["all_data"] = all_data
            st.session_state["analysis_time"] = datetime.now().strftime("%H:%M:%S")

            # Build chat context
            try:
                from aibot.llm.chat import create_chat_context
                st.session_state["chat_context"] = create_chat_context(midcap, smallcap, all_data)
            except Exception:
                st.session_state["chat_context"] = None

            st.success(f"Analysis complete! Found top picks at {st.session_state['analysis_time']}")
        except Exception as e:
            st.error(f"Pipeline error: {e}")
            import traceback
            st.code(traceback.format_exc())


def _render_scoreboard(midcap: list, smallcap: list):
    """Render the scoreboard tab with top picks."""
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 5 Midcap")
        for i, stock in enumerate(midcap, 1):
            _render_stock_card(i, stock)

    with col2:
        st.subheader("Top 5 Smallcap")
        for i, stock in enumerate(smallcap, 1):
            _render_stock_card(i, stock)


def _render_stock_card(rank: int, stock: dict):
    """Render a single stock card."""
    score = stock.get("swing_score", 0)
    color = "green" if score >= 70 else ("orange" if score >= 50 else "red")

    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 2, 1])

        with c1:
            st.metric(f"#{rank}", stock.get("symbol", "N/A"))

        with c2:
            trend = stock.get("trend", {})
            st.markdown(f"**Score: :{color}[{score}/100]** | Price: INR {stock.get('price', 0)}")
            st.caption(
                f"5D: {trend.get('pct_5d', 0):+.1f}% | "
                f"RSI: {stock.get('rsi', 0)} | "
                f"MACD: {stock.get('macd', {}).get('status', 'N/A')} | "
                f"Vol: {stock.get('volume_expansion', 1.0):.1f}x"
            )

        with c3:
            levels = stock.get("levels", {})
            st.caption(f"S: {levels.get('support', 'N/A')}")
            st.caption(f"R: {levels.get('resistance', 'N/A')}")

        rationale = stock.get("rationale", "")
        if rationale:
            st.caption(f"*{rationale}*")


def _render_detail_view(midcap: list, smallcap: list):
    """Render detailed view for a selected stock."""
    all_stocks = midcap + smallcap
    symbols = [s.get("symbol", "") for s in all_stocks]

    selected = st.selectbox("Select Stock", symbols)
    stock = next((s for s in all_stocks if s.get("symbol") == selected), None)

    if stock is None:
        return

    # ─── Header ───
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Swing Score", f"{stock.get('swing_score', 0)}/100")
    col2.metric("Price", f"INR {stock.get('price', 0)}")
    col3.metric("RSI", stock.get("rsi", 0))
    col4.metric("ATR%", f"{stock.get('atr_pct', 0)}%")

    # ─── Component Scores Bar Chart ───
    st.subheader("Score Breakdown")
    norm = stock.get("normalized_scores", {})
    if norm:
        from config import WEIGHTS
        fig = go.Figure()
        components = list(norm.keys())
        scores = [norm[k] for k in components]
        weights = [WEIGHTS.get(k, 0) * 100 for k in components]
        weighted = [norm[k] * WEIGHTS.get(k, 0) for k in components]

        fig.add_trace(go.Bar(
            x=[c.title() for c in components],
            y=scores,
            name="Raw Score (0-100)",
            marker_color="steelblue",
        ))
        fig.add_trace(go.Bar(
            x=[c.title() for c in components],
            y=weighted,
            name="Weighted Contribution",
            marker_color="orange",
        ))
        fig.update_layout(barmode="group", height=350, margin=dict(t=30))
        st.plotly_chart(fig, use_container_width=True)

    # ─── Details ───
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Technical Indicators")
        trend = stock.get("trend", {})
        macd = stock.get("macd", {})
        st.markdown(f"""
| Indicator | Value |
|-----------|-------|
| Trend 5D | {trend.get('pct_5d', 0):+.1f}% |
| Trend 10D | {trend.get('pct_10d', 0):+.1f}% |
| Trend 20D | {trend.get('pct_20d', 0):+.1f}% |
| EMA Aligned | {'Yes' if trend.get('ema_aligned') else 'No'} |
| RSI (14) | {stock.get('rsi', 0)} |
| MACD Status | {macd.get('status', 'N/A')} |
| MACD Histogram | {macd.get('histogram', 0)} |
| ATR% | {stock.get('atr_pct', 0)}% |
| Volume Expansion | {stock.get('volume_expansion', 1.0):.1f}x |
| Delivery% | {stock.get('delivery_pct', 0)}% |
""")

    with col2:
        st.subheader("Swing Levels")
        levels = stock.get("levels", {})
        pivots = levels.get("pivot_points", {})
        st.markdown(f"""
| Level | Price |
|-------|-------|
| Resistance | {levels.get('resistance', 'N/A')} |
| R1 (Pivot) | {pivots.get('r1', 'N/A')} |
| Pivot | {pivots.get('pivot', 'N/A')} |
| S1 (Pivot) | {pivots.get('s1', 'N/A')} |
| Support | {levels.get('support', 'N/A')} |
""")
        sentiment = stock.get("sentiment", {})
        st.subheader("Sentiment")
        st.markdown(f"**{sentiment.get('label', 'N/A').title()}** (confidence: {sentiment.get('score', 0):.2f})")

        if sentiment.get("details"):
            for d in sentiment["details"][:3]:
                st.caption(f"- [{d.get('label', '')}] {d.get('headline', '')[:80]}")

    # ─── Rationale ───
    rationale = stock.get("rationale", "")
    if rationale:
        st.subheader("Trading Rationale")
        st.info(rationale)


def _render_chat():
    """Render the chat interface for Q&A with AIBOT."""
    st.subheader("Chat with AIBOT")

    if "chat_context" not in st.session_state or st.session_state["chat_context"] is None:
        st.warning("Run the analysis first to enable chat. The LLM needs analysis data as context.")
        return

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Display chat history
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask about the analysis (e.g., 'Why is X ranked #1?')"):
        # Add user message
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get LLM response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    from aibot.llm.chat import ask_question
                    response = ask_question(
                        question=prompt,
                        system_context=st.session_state["chat_context"],
                        conversation_history=st.session_state["chat_history"][:-1],
                    )
                except Exception as e:
                    response = f"Error: {e}. Make sure your API key is configured in .env"

                st.markdown(response)
                st.session_state["chat_history"].append({"role": "assistant", "content": response})

    # Quick questions
    st.caption("Try asking:")
    cols = st.columns(3)
    suggestions = [
        "Which stock has the best risk/reward?",
        "Compare the top midcap and smallcap picks",
        "What sectors are showing the most momentum?",
    ]
    for col, suggestion in zip(cols, suggestions):
        if col.button(suggestion, use_container_width=True):
            st.session_state["_pending_question"] = suggestion
            st.rerun()


def _show_instructions():
    """Show getting started instructions."""
    st.markdown("""
### Getting Started

1. **Configure API Key** — Edit `.env` with your Anthropic or OpenAI API key for LLM features
2. **Click Run Analysis** — The pipeline will:
   - Fetch Nifty Midcap 150 + Smallcap 250 constituents
   - Download price data for ~400 stocks
   - Compute RSI, MACD, ATR, trends, volume expansion
   - Analyze news sentiment via FinBERT
   - Apply filters and compute Swing Scores
   - Generate AI-powered trading rationales
3. **Explore Results** — View scoreboard, detailed breakdowns, and chat with the AI

### CLI Usage
```bash
python main.py                    # Full analysis with sentiment
python main.py --skip-sentiment   # Skip FinBERT (faster)
streamlit run app.py              # Launch this dashboard
```
""")


if __name__ == "__main__":
    main()

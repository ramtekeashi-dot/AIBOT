"""AIBOT - Dark Trading Terminal Dashboard for NSE Swing Trading Analysis."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="AIBOT - Swing Trading Terminal",
    page_icon="https://img.icons8.com/color/48/combo-chart.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════
# SECTION 1: THEME & COLOR SYSTEM
# ═══════════════════════════════════════════════════════════════════

THEMES = {
    "dark": {
        "bg_primary": "#0a0e17",
        "bg_secondary": "#111827",
        "bg_tertiary": "#1a2332",
        "text_primary": "#e0e6ed",
        "text_secondary": "#8892a4",
        "text_muted": "#4a5568",
        "border": "#1e293b",
        "border_active": "#334155",
    },
    "light": {
        "bg_primary": "#f8fafc",
        "bg_secondary": "#ffffff",
        "bg_tertiary": "#f1f5f9",
        "text_primary": "#1a202c",
        "text_secondary": "#4a5568",
        "text_muted": "#a0aec0",
        "border": "#e2e8f0",
        "border_active": "#cbd5e0",
    },
}

GLOW_COLORS = {
    "green":  {"color": "#00d4aa", "rgb": "0, 212, 170"},
    "red":    {"color": "#ff4757", "rgb": "255, 71, 87"},
    "blue":   {"color": "#3b82f6", "rgb": "59, 130, 246"},
    "yellow": {"color": "#f59e0b", "rgb": "245, 158, 11"},
}


def get_theme():
    return st.session_state.get("theme", "dark")


def toggle_theme():
    st.session_state["theme"] = "light" if get_theme() == "dark" else "dark"


# ═══════════════════════════════════════════════════════════════════
# SECTION 2: COLOR MAPPING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def score_to_glow(score: float) -> str:
    if score >= 70: return "green"
    if score >= 50: return "yellow"
    return "red"


def sentiment_to_glow(label: str) -> str:
    return {"positive": "green", "neutral": "blue", "negative": "red"}.get(label, "blue")


def macd_to_glow(status: str) -> str:
    if status in ("bullish_crossover", "bullish"): return "green"
    if status in ("bearish_crossover", "bearish"): return "red"
    return "blue"


def rsi_to_glow(rsi: float) -> str:
    if rsi > 65: return "yellow"
    if rsi < 35: return "red"
    return "green"


def atr_to_glow(atr_pct: float) -> str:
    if atr_pct > 4.0: return "yellow"
    if atr_pct < 1.0: return "blue"
    return "green"


def trend_to_glow(pct_5d: float, ema_aligned: bool) -> str:
    if ema_aligned and pct_5d > 0: return "green"
    if pct_5d < -2: return "red"
    if pct_5d < 0: return "yellow"
    return "blue"


def volume_to_glow(expansion: float) -> str:
    if expansion >= 1.5: return "green"
    if expansion >= 1.0: return "blue"
    return "red"


def gc(name: str) -> str:
    """Get glow color hex by name."""
    return GLOW_COLORS.get(name, GLOW_COLORS["blue"])["color"]


def gr(name: str) -> str:
    """Get glow color RGB by name."""
    return GLOW_COLORS.get(name, GLOW_COLORS["blue"])["rgb"]


# ═══════════════════════════════════════════════════════════════════
# SECTION 3: CSS STYLESHEET
# ═══════════════════════════════════════════════════════════════════

def generate_css() -> str:
    t = THEMES[get_theme()]
    is_dark = get_theme() == "dark"
    glow_mult = "0.3" if is_dark else "0.12"
    text_shadow = "0 0 10px" if is_dark else "none"

    return f"""<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

:root {{
    --bg-primary: {t['bg_primary']};
    --bg-secondary: {t['bg_secondary']};
    --bg-tertiary: {t['bg_tertiary']};
    --text-primary: {t['text_primary']};
    --text-secondary: {t['text_secondary']};
    --text-muted: {t['text_muted']};
    --border: {t['border']};
    --border-active: {t['border_active']};
    --glow-mult: {glow_mult};
}}

.stApp {{
    background-color: var(--bg-primary) !important;
    font-family: 'Inter', sans-serif;
}}

section[data-testid="stSidebar"] {{
    background-color: var(--bg-secondary) !important;
    border-right: 1px solid var(--border) !important;
}}
section[data-testid="stSidebar"] .stSlider label p {{
    color: var(--text-secondary) !important;
    font-size: 0.8rem !important;
}}

button[data-baseweb="tab"] {{
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
}}

::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: var(--bg-primary); }}
::-webkit-scrollbar-thumb {{ background: var(--border-active); border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--text-muted); }}

hr {{ border-color: var(--border) !important; opacity: 0.5; }}

/* ─── STOCK CARD ─── */
.stock-card {{
    background: var(--bg-secondary);
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 12px;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}}
.stock-card:hover {{
    background: var(--bg-tertiary);
    transform: translateX(3px);
}}

/* ─── GLOW CLASSES ─── */
.glow-green-border {{
    border-left: 4px solid {gc('green')};
    box-shadow: -4px 0 20px rgba({gr('green')}, var(--glow-mult)),
                inset -4px 0 20px rgba({gr('green')}, 0.05);
}}
.glow-red-border {{
    border-left: 4px solid {gc('red')};
    box-shadow: -4px 0 20px rgba({gr('red')}, var(--glow-mult)),
                inset -4px 0 20px rgba({gr('red')}, 0.05);
}}
.glow-blue-border {{
    border-left: 4px solid {gc('blue')};
    box-shadow: -4px 0 20px rgba({gr('blue')}, var(--glow-mult)),
                inset -4px 0 20px rgba({gr('blue')}, 0.05);
}}
.glow-yellow-border {{
    border-left: 4px solid {gc('yellow')};
    box-shadow: -4px 0 20px rgba({gr('yellow')}, var(--glow-mult)),
                inset -4px 0 20px rgba({gr('yellow')}, 0.05);
}}

.glow-green-text  {{ color: {gc('green')};  text-shadow: {text_shadow} rgba({gr('green')}, 0.5); }}
.glow-red-text    {{ color: {gc('red')};    text-shadow: {text_shadow} rgba({gr('red')}, 0.5); }}
.glow-blue-text   {{ color: {gc('blue')};   text-shadow: {text_shadow} rgba({gr('blue')}, 0.5); }}
.glow-yellow-text {{ color: {gc('yellow')}; text-shadow: {text_shadow} rgba({gr('yellow')}, 0.5); }}

/* ─── SCORE BADGE ─── */
.score-badge {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.8rem;
    font-weight: 700;
    line-height: 1;
    letter-spacing: -1px;
}}
.score-sub {{
    font-size: 0.65rem;
    color: var(--text-muted);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    font-family: 'JetBrains Mono', monospace;
}}

.rank-badge {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px; height: 28px;
    border-radius: 50%;
    font-weight: 700;
    font-size: 0.85rem;
    font-family: 'JetBrains Mono', monospace;
    background: var(--bg-tertiary);
    color: var(--text-primary);
    border: 1px solid var(--border-active);
}}

.stock-sym {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.05rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    color: var(--text-primary);
}}

.pill {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 5px;
    font-size: 0.72rem;
    font-family: 'JetBrains Mono', monospace;
    margin-right: 5px;
    margin-top: 6px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    transition: all 0.2s;
}}

.metric-card {{
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 18px;
    text-align: center;
    transition: all 0.3s;
}}
.metric-card:hover {{ border-color: var(--border-active); }}
.metric-val {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.5rem;
    font-weight: 700;
}}
.metric-lbl {{
    font-size: 0.65rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 4px;
    font-family: 'JetBrains Mono', monospace;
}}

.tech-tbl {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0 4px;
}}
.tech-tbl tr {{
    background: var(--bg-secondary);
    transition: background 0.2s;
}}
.tech-tbl tr:hover {{ background: var(--bg-tertiary); }}
.tech-tbl td {{
    padding: 8px 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    border: none;
}}
.tech-tbl td:first-child {{
    color: var(--text-secondary);
    border-radius: 6px 0 0 6px;
}}
.tech-tbl td:last-child {{
    text-align: right;
    font-weight: 600;
    border-radius: 0 6px 6px 0;
}}

.sec-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 10px;
}}
.sec-tag {{
    padding: 2px 10px;
    border-radius: 4px;
    font-size: 0.65rem;
    font-weight: 500;
    letter-spacing: 1px;
}}

.sent-card {{
    padding: 14px;
    background: var(--bg-secondary);
    border-radius: 8px;
    margin-top: 8px;
}}

.hdr-title {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    color: #00d4aa;
    text-shadow: 0 0 25px rgba(0, 212, 170, 0.3);
    letter-spacing: 3px;
}}
.hdr-sub {{
    color: var(--text-secondary);
    font-size: 0.75rem;
    letter-spacing: 1.5px;
    font-family: 'JetBrains Mono', monospace;
    margin-top: 2px;
}}

.signal-box {{
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    margin-top: 12px;
    font-size: 0.88rem;
    line-height: 1.6;
}}

div[data-testid="stChatMessage"] {{
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}}

#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
</style>"""


# ═══════════════════════════════════════════════════════════════════
# SECTION 4: HELPER RENDERERS
# ═══════════════════════════════════════════════════════════════════

def _render_header():
    last_run = st.session_state.get("analysis_timestamp", None)
    ts = f"LAST RUN: {last_run}" if last_run else datetime.now().strftime("%Y-%m-%d")
    st.markdown(f"""
    <div style="margin-bottom:24px;">
        <div class="hdr-title">AIBOT</div>
        <div class="hdr-sub">
            NSE SWING TRADING ANALYST &nbsp;&bull;&nbsp;
            MIDCAP 150 + SMALLCAP 250 &nbsp;&bull;&nbsp;
            {ts}
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_metric_card(label: str, value: str, glow: str = "blue"):
    color = gc(glow)
    st.markdown(f"""
    <div class="metric-card" style="border-color:{color}30;">
        <div class="metric-lbl">{label}</div>
        <div class="metric-val glow-{glow}-text">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def _render_tech_row(label: str, value: str, glow: str = "blue") -> str:
    color = gc(glow)
    return f'<tr><td>{label}</td><td style="color:{color};">{value}</td></tr>'


def _get_plotly_layout() -> dict:
    if get_theme() == "dark":
        return {
            "template": "plotly_dark",
            "paper_bgcolor": "#0a0e17",
            "plot_bgcolor": "#111827",
            "font": {"family": "JetBrains Mono, monospace", "color": "#e0e6ed", "size": 11},
            "xaxis": {"gridcolor": "#1e293b", "zerolinecolor": "#1e293b"},
            "yaxis": {"gridcolor": "#1e293b", "zerolinecolor": "#1e293b"},
            "margin": {"t": 30, "b": 30, "l": 40, "r": 20},
        }
    return {
        "template": "plotly_white",
        "paper_bgcolor": "#ffffff",
        "plot_bgcolor": "#f8fafc",
        "font": {"family": "JetBrains Mono, monospace", "color": "#1a202c", "size": 11},
        "margin": {"t": 30, "b": 30, "l": 40, "r": 20},
    }


def _render_price_chart(stock: dict):
    """Render HD candlestick chart with volume, S/R lines, and trade level overlays."""
    ohlcv = stock.get("ohlcv", {})
    if not ohlcv or not ohlcv.get("dates"):
        st.caption("No OHLCV data available for chart. Run a new analysis to generate charts.")
        return

    dates = ohlcv["dates"]
    opens = ohlcv["open"]
    highs = ohlcv["high"]
    lows = ohlcv["low"]
    closes = ohlcv["close"]
    volumes = ohlcv["volume"]

    # Volume bar colors (green = bullish candle, red = bearish)
    vol_colors = [
        gc("green") if c >= o else gc("red")
        for o, c in zip(opens, closes)
    ]

    is_dark = get_theme() == "dark"
    bg_paper = "#0a0e17" if is_dark else "#ffffff"
    bg_plot = "#111827" if is_dark else "#f8fafc"
    grid_color = "#1e293b" if is_dark else "#e2e8f0"
    text_color = "#e0e6ed" if is_dark else "#1a202c"

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.8, 0.2], vertical_spacing=0.02,
    )

    # ── Candlestick trace ──
    fig.add_trace(go.Candlestick(
        x=dates, open=opens, high=highs, low=lows, close=closes,
        increasing_line_color=gc("green"), decreasing_line_color=gc("red"),
        increasing_fillcolor=gc("green"), decreasing_fillcolor=gc("red"),
        name="Price", showlegend=False,
    ), row=1, col=1)

    # ── EMA Trend Lines ──
    close_series = pd.Series(closes, dtype=float)
    if len(close_series) >= 20:
        ema20 = close_series.ewm(span=20, adjust=False).mean().round(2).tolist()
        fig.add_trace(go.Scatter(
            x=dates, y=ema20, mode="lines", name="EMA 20",
            line=dict(color=gc("yellow"), width=1.5, dash="solid"),
            opacity=0.8,
        ), row=1, col=1)
    if len(close_series) >= 50:
        ema50 = close_series.ewm(span=50, adjust=False).mean().round(2).tolist()
        fig.add_trace(go.Scatter(
            x=dates, y=ema50, mode="lines", name="EMA 50",
            line=dict(color="#a78bfa", width=1.5, dash="solid"),
            opacity=0.8,
        ), row=1, col=1)

    # ── Volume bars ──
    fig.add_trace(go.Bar(
        x=dates, y=volumes, marker_color=vol_colors,
        opacity=0.5, name="Volume", showlegend=False,
    ), row=2, col=1)

    # ── Helper: add horizontal level line ──
    def add_level_line(y_val, label, color, dash="dash", width=1):
        if not y_val or y_val == 0:
            return
        fig.add_hline(
            y=y_val, line_dash=dash, line_color=color, line_width=width,
            annotation_text=f" {label}: {y_val}",
            annotation_position="right",
            annotation_font_size=10,
            annotation_font_color=color,
            row=1, col=1,
        )

    # ── Support / Resistance lines ──
    levels = stock.get("levels", {})
    add_level_line(levels.get("support"), "Support", gc("green"), "dot", 1)
    add_level_line(levels.get("resistance"), "Resistance", gc("red"), "dot", 1)

    # ── Pivot point lines ──
    pivots = levels.get("pivot_points", {})
    add_level_line(pivots.get("pivot"), "Pivot", gc("blue"), "dash", 1)
    add_level_line(pivots.get("s1"), "S1", "#22c55e", "dot", 1)
    add_level_line(pivots.get("s2"), "S2", "#16a34a", "dot", 1)
    add_level_line(pivots.get("r1"), "R1", "#fb923c", "dot", 1)
    add_level_line(pivots.get("r2"), "R2", "#ef4444", "dot", 1)

    # ── Trade level lines (Entry/SL/TP) ──
    tl = stock.get("trade_levels", {})
    add_level_line(tl.get("entry"), "ENTRY", gc("blue"), "solid", 2)
    add_level_line(tl.get("sl"), "SL", gc("red"), "solid", 2)
    add_level_line(tl.get("tp1"), "TP1", "#34d399", "solid", 1)
    add_level_line(tl.get("tp2"), "TP2", "#10b981", "solid", 1)
    add_level_line(tl.get("tp3"), "TP3", "#059669", "solid", 1)

    # ── Layout ──
    symbol = stock.get("symbol", "")
    fig.update_layout(
        title=None,
        paper_bgcolor=bg_paper,
        plot_bgcolor=bg_plot,
        font=dict(family="JetBrains Mono, monospace", color=text_color, size=11),
        height=600,
        margin=dict(t=10, b=30, l=50, r=120),
        xaxis_rangeslider_visible=False,
        xaxis2_rangeslider_visible=False,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=10)),
    )

    # Style axes
    for axis in ["xaxis", "xaxis2"]:
        fig.update_layout(**{axis: dict(gridcolor=grid_color, showgrid=False)})
    fig.update_layout(
        yaxis=dict(gridcolor=grid_color, title="Price (INR)", side="right"),
        yaxis2=dict(gridcolor=grid_color, title="Vol", side="right", showgrid=False),
    )

    st.plotly_chart(
        fig, width="stretch",
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        },
    )


# ═══════════════════════════════════════════════════════════════════
# SECTION 5: COMPONENT RENDERERS
# ═══════════════════════════════════════════════════════════════════

def _render_stock_card(rank: int, stock: dict):
    score = stock.get("swing_score", 0)
    glow = score_to_glow(score)
    glow_color = gc(glow)
    symbol = stock.get("symbol", "N/A")
    price = stock.get("price", 0)
    trend = stock.get("trend", {})
    macd = stock.get("macd", {})
    levels = stock.get("levels", {})
    rsi_val = stock.get("rsi", 50)

    t_glow = trend_to_glow(trend.get("pct_5d", 0), trend.get("ema_aligned", False))
    r_glow = rsi_to_glow(rsi_val)
    m_glow = macd_to_glow(macd.get("status", "neutral"))
    v_glow = volume_to_glow(stock.get("volume_expansion", 1.0))

    bar_w = min(score, 100)

    st.markdown(f"""
    <div class="stock-card glow-{glow}-border">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
                <span class="rank-badge">{rank}</span>
                <span class="stock-sym" style="margin-left:10px;">{symbol}</span>
                <span style="color:var(--text-secondary); margin-left:10px; font-size:0.82rem;
                             font-family:'JetBrains Mono',monospace;">
                    INR {price:,.2f}
                </span>
            </div>
            <div style="text-align:right;">
                <div class="score-badge glow-{glow}-text">{score:.1f}</div>
                <div class="score-sub">SWING SCORE</div>
                <div style="width:80px; height:4px; background:var(--bg-tertiary); border-radius:2px; margin-top:5px;">
                    <div style="width:{bar_w}%; height:100%; background:{glow_color}; border-radius:2px;
                                box-shadow: 0 0 10px {glow_color}50;"></div>
                </div>
            </div>
        </div>
        <div>
            <span class="pill" style="border-color:{gc(t_glow)}50; color:{gc(t_glow)};">
                5D: {trend.get('pct_5d', 0):+.1f}%
            </span>
            <span class="pill" style="border-color:{gc(r_glow)}50; color:{gc(r_glow)};">
                RSI: {rsi_val:.0f}
            </span>
            <span class="pill" style="border-color:{gc(m_glow)}50; color:{gc(m_glow)};">
                {macd.get('status', 'N/A').replace('_', ' ').title()}
            </span>
            <span class="pill" style="border-color:{gc(v_glow)}50; color:{gc(v_glow)};">
                Vol: {stock.get('volume_expansion', 1.0):.1f}x
            </span>
        </div>
        <div style="margin-top:8px; font-size:0.72rem; font-family:'JetBrains Mono',monospace; color:var(--text-muted);">
            S: {levels.get('support', 'N/A')} &nbsp;&bull;&nbsp; R: {levels.get('resistance', 'N/A')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    rationale = stock.get("rationale", "")
    if rationale:
        with st.expander("Trading Signal", expanded=False):
            # Render as styled monospace text to prevent LLM markdown from blowing up layout
            import html as html_mod
            safe_text = html_mod.escape(rationale).replace("\n", "<br>")
            st.markdown(
                f'<div style="font-family:\'JetBrains Mono\',monospace; font-size:0.8rem; '
                f'line-height:1.6; color:var(--text-secondary);">{safe_text}</div>',
                unsafe_allow_html=True,
            )


def _render_scoreboard(midcap: list, smallcap: list):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="sec-label">
            MIDCAP TOP 5
            <span class="sec-tag" style="background:{gc('green')}15; color:{gc('green')};">NIFTY MIDCAP 150</span>
        </div>
        """, unsafe_allow_html=True)
        for i, stock in enumerate(midcap, 1):
            _render_stock_card(i, stock)
    with col2:
        st.markdown(f"""
        <div class="sec-label">
            SMALLCAP TOP 5
            <span class="sec-tag" style="background:{gc('blue')}15; color:{gc('blue')};">NIFTY SMALLCAP 250</span>
        </div>
        """, unsafe_allow_html=True)
        for i, stock in enumerate(smallcap, 1):
            _render_stock_card(i, stock)


def _render_detail_view(midcap: list, smallcap: list):
    all_stocks = midcap + smallcap
    symbols = [s.get("symbol", "") for s in all_stocks]
    selected = st.selectbox("Select Stock", symbols, label_visibility="collapsed")
    stock = next((s for s in all_stocks if s.get("symbol") == selected), None)
    if stock is None:
        return

    score = stock.get("swing_score", 0)
    rsi_val = stock.get("rsi", 0)
    atr_val = stock.get("atr_pct", 0)
    price = stock.get("price", 0)

    # Header Metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1: _render_metric_card("SWING SCORE", f"{score:.1f}/100", score_to_glow(score))
    with c2: _render_metric_card("PRICE", f"INR {price:,.2f}", "blue")
    with c3: _render_metric_card("RSI (14)", f"{rsi_val:.0f}", rsi_to_glow(rsi_val))
    with c4: _render_metric_card("ATR%", f"{atr_val:.1f}%", atr_to_glow(atr_val))

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # ── HD Candlestick Chart ──
    st.markdown('<div class="sec-label">PRICE ACTION</div>', unsafe_allow_html=True)
    _render_price_chart(stock)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # Charts
    norm = stock.get("normalized_scores", {})
    if norm:
        from config import WEIGHTS
        ch1, ch2 = st.columns(2)

        with ch1:
            st.markdown('<div class="sec-label">SCORE BREAKDOWN</div>', unsafe_allow_html=True)
            components = list(norm.keys())
            scores_list = [norm[k] for k in components]
            weighted = [norm[k] * WEIGHTS.get(k, 0) for k in components]
            bar_colors = [gc(score_to_glow(v)) for v in scores_list]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[c.upper() for c in components], y=scores_list,
                name="Raw Score", marker_color=bar_colors, opacity=0.85,
            ))
            fig.add_trace(go.Bar(
                x=[c.upper() for c in components], y=weighted,
                name="Weighted", marker_color="rgba(59, 130, 246, 0.5)",
                marker_line_color="#3b82f6", marker_line_width=1,
            ))
            layout = _get_plotly_layout()
            layout["barmode"] = "group"
            layout["height"] = 340
            layout["legend"] = {"orientation": "h", "yanchor": "bottom", "y": 1.02, "font": {"size": 10}}
            fig.update_layout(**layout)
            st.plotly_chart(fig, width="stretch")

        with ch2:
            st.markdown('<div class="sec-label">SCORE PROFILE</div>', unsafe_allow_html=True)
            cats = [c.title() for c in norm.keys()] + [list(norm.keys())[0].title()]
            vals = list(norm.values()) + [list(norm.values())[0]]
            fig_r = go.Figure()
            fig_r.add_trace(go.Scatterpolar(
                r=vals, theta=cats, fill="toself",
                fillcolor=f"rgba({gr('green')}, 0.12)",
                line=dict(color=gc("green"), width=2), name="Score",
            ))
            rl = _get_plotly_layout()
            bg = "#111827" if get_theme() == "dark" else "#f8fafc"
            grid_c = "#1e293b" if get_theme() == "dark" else "#e2e8f0"
            rl["polar"] = {
                "radialaxis": {"visible": True, "range": [0, 100], "gridcolor": grid_c},
                "angularaxis": {"gridcolor": grid_c},
                "bgcolor": bg,
            }
            rl["height"] = 340
            rl["showlegend"] = False
            fig_r.update_layout(**rl)
            st.plotly_chart(fig_r, width="stretch")

    # Technical Indicators + Swing Levels
    tc1, tc2 = st.columns(2)
    trend = stock.get("trend", {})
    macd = stock.get("macd", {})

    with tc1:
        st.markdown('<div class="sec-label">TECHNICAL INDICATORS</div>', unsafe_allow_html=True)
        rows = "".join([
            _render_tech_row("Trend 5D", f"{trend.get('pct_5d', 0):+.1f}%",
                           trend_to_glow(trend.get("pct_5d", 0), trend.get("ema_aligned", False))),
            _render_tech_row("Trend 10D", f"{trend.get('pct_10d', 0):+.1f}%", "blue"),
            _render_tech_row("Trend 20D", f"{trend.get('pct_20d', 0):+.1f}%", "blue"),
            _render_tech_row("EMA Aligned", "YES" if trend.get("ema_aligned") else "NO",
                           "green" if trend.get("ema_aligned") else "red"),
            _render_tech_row("RSI (14)", f"{rsi_val:.0f}", rsi_to_glow(rsi_val)),
            _render_tech_row("MACD", macd.get("status", "N/A").replace("_", " ").title(),
                           macd_to_glow(macd.get("status", "neutral"))),
            _render_tech_row("MACD Hist", f"{macd.get('histogram', 0):+.2f}",
                           "green" if macd.get("histogram", 0) > 0 else "red"),
            _render_tech_row("ATR%", f"{atr_val:.1f}%", atr_to_glow(atr_val)),
            _render_tech_row("Volume", f"{stock.get('volume_expansion', 1.0):.1f}x",
                           volume_to_glow(stock.get("volume_expansion", 1.0))),
            _render_tech_row("Delivery%", f"{stock.get('delivery_pct', 0):.0f}%",
                           "green" if stock.get("delivery_pct", 0) > 40 else "blue"),
        ])
        st.markdown(f'<table class="tech-tbl">{rows}</table>', unsafe_allow_html=True)

    with tc2:
        st.markdown('<div class="sec-label">SWING LEVELS</div>', unsafe_allow_html=True)
        levels = stock.get("levels", {})
        pivots = levels.get("pivot_points", {})
        lvl_rows = "".join([
            _render_tech_row("Resistance", str(levels.get("resistance", "N/A")), "red"),
            _render_tech_row("R2 (Pivot)", str(pivots.get("r2", "N/A")), "red"),
            _render_tech_row("R1 (Pivot)", str(pivots.get("r1", "N/A")), "yellow"),
            _render_tech_row("Pivot", str(pivots.get("pivot", "N/A")), "blue"),
            _render_tech_row("S1 (Pivot)", str(pivots.get("s1", "N/A")), "yellow"),
            _render_tech_row("S2 (Pivot)", str(pivots.get("s2", "N/A")), "green"),
            _render_tech_row("Support", str(levels.get("support", "N/A")), "green"),
        ])
        st.markdown(f'<table class="tech-tbl">{lvl_rows}</table>', unsafe_allow_html=True)

        # Sentiment
        sent = stock.get("sentiment", {})
        s_glow = sentiment_to_glow(sent.get("label", "neutral"))
        s_color = gc(s_glow)
        st.markdown(f"""
        <div class="sent-card" style="border-left:3px solid {s_color}; margin-top:16px;">
            <div style="font-size:0.65rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:1.5px;
                        font-family:'JetBrains Mono',monospace;">SENTIMENT</div>
            <div style="font-size:1.1rem; font-weight:600; color:{s_color}; margin-top:4px;
                        font-family:'JetBrains Mono',monospace;">
                {sent.get('label', 'N/A').upper()}
                <span style="font-size:0.78rem; color:var(--text-secondary); margin-left:10px;">
                    {sent.get('score', 0):.0%} confidence
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if sent.get("details"):
            for d in sent["details"][:5]:
                label = d.get("label", "neutral")
                headline = d.get("headline", "")
                url = d.get("url", "")
                lbl_color = gc(sentiment_to_glow(label))
                if url:
                    st.markdown(
                        f'<div style="font-size:0.78rem; margin-top:4px; line-height:1.4;">'
                        f'<span style="color:{lbl_color}; font-weight:600; font-family:\'JetBrains Mono\',monospace;">'
                        f'[{label.upper()}]</span> '
                        f'<a href="{url}" target="_blank" style="color:var(--text-secondary); text-decoration:none;">'
                        f'{headline}</a></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div style="font-size:0.78rem; margin-top:4px; line-height:1.4;">'
                        f'<span style="color:{lbl_color}; font-weight:600; font-family:\'JetBrains Mono\',monospace;">'
                        f'[{label.upper()}]</span> '
                        f'<span style="color:var(--text-secondary);">{headline}</span></div>',
                        unsafe_allow_html=True,
                    )

    # Trading Signal
    rationale = stock.get("rationale", "")
    if rationale:
        st.markdown('<div class="sec-label" style="margin-top:20px;">TRADING SIGNAL</div>', unsafe_allow_html=True)
        import html as html_mod
        safe_rationale = html_mod.escape(rationale).replace("\n", "<br>")
        st.markdown(
            f'<div class="signal-box" style="font-family:\'JetBrains Mono\',monospace; '
            f'font-size:0.82rem; line-height:1.7;">{safe_rationale}</div>',
            unsafe_allow_html=True,
        )


def _render_chat():
    st.markdown("""
    <div class="sec-label" style="margin-bottom:12px;">
        AIBOT TERMINAL &nbsp;&bull;&nbsp; MULTI-TURN Q&A
    </div>
    """, unsafe_allow_html=True)

    if "chat_context" not in st.session_state or st.session_state["chat_context"] is None:
        st.warning("Run the analysis first to enable chat.")
        return

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    pending = st.session_state.pop("_pending_question", None)
    if pending:
        _process_chat_question(pending)

    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about the analysis (e.g., 'Why is X ranked #1?')"):
        _process_chat_question(prompt)
        st.rerun()

    st.caption("Try asking:")
    cols = st.columns(3)
    suggestions = [
        "Which stock has the best risk/reward?",
        "Compare the top midcap and smallcap picks",
        "What sectors are showing the most momentum?",
    ]
    for col, suggestion in zip(cols, suggestions):
        if col.button(suggestion, key=f"suggest_{suggestion[:10]}", width="stretch"):
            st.session_state["_pending_question"] = suggestion
            st.rerun()


# ═══════════════════════════════════════════════════════════════════
# SECTION 6: PIPELINE / HISTORY / CHAT (PRESERVED)
# ═══════════════════════════════════════════════════════════════════

def _run_analysis():
    with st.spinner("Running AIBOT analysis pipeline... This may take a few minutes."):
        try:
            from main import run_pipeline
            skip = st.session_state.get("skip_sentiment", False)
            midcap, smallcap, all_data = run_pipeline(skip_sentiment=skip)

            st.session_state["midcap_top5"] = midcap
            st.session_state["smallcap_top5"] = smallcap
            st.session_state["all_data"] = all_data
            st.session_state["analysis_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            try:
                from aibot.output.history import save_analysis
                save_analysis(midcap, smallcap, all_data)
            except Exception as e:
                print(f"[WARN] Failed to save history: {e}")

            try:
                from aibot.llm.chat import create_chat_context
                st.session_state["chat_context"] = create_chat_context(midcap, smallcap, all_data)
            except Exception:
                st.session_state["chat_context"] = None

            st.success(f"Analysis complete at {st.session_state['analysis_timestamp']}")
        except Exception as e:
            st.error(f"Pipeline error: {e}")
            import traceback
            st.code(traceback.format_exc())


def _process_chat_question(question: str):
    st.session_state["chat_history"].append({"role": "user", "content": question})
    try:
        from aibot.llm.chat import ask_question
        response = ask_question(
            question=question,
            system_context=st.session_state["chat_context"],
            conversation_history=st.session_state["chat_history"][:-1],
        )
    except Exception as e:
        response = f"Error: {e}. Make sure your API key is configured in .env"
    st.session_state["chat_history"].append({"role": "assistant", "content": response})


def _try_load_latest():
    try:
        from aibot.output.history import load_latest_analysis
        data = load_latest_analysis()
        if data:
            st.session_state["midcap_top5"] = data["midcap_top5"]
            st.session_state["smallcap_top5"] = data["smallcap_top5"]
            st.session_state["analysis_timestamp"] = data["timestamp"]
            try:
                from aibot.llm.chat import create_chat_context
                st.session_state["chat_context"] = create_chat_context(
                    data["midcap_top5"], data["smallcap_top5"]
                )
            except Exception:
                st.session_state["chat_context"] = None
    except Exception:
        pass


def _render_history_selector():
    try:
        from aibot.output.history import list_history, load_analysis_by_file
        runs = list_history()
    except Exception:
        runs = []

    if not runs:
        st.caption("No saved runs yet.")
        return

    options = ["-- Select past run --"] + [r["display_name"] for r in runs]
    selected = st.selectbox("Load Past Run", options, key="history_selector", label_visibility="collapsed")

    if selected != "-- Select past run --":
        idx = options.index(selected) - 1
        if st.button("Load Selected Run", key="load_history_btn"):
            run = runs[idx]
            data = load_analysis_by_file(run["filename"])
            if data:
                st.session_state["midcap_top5"] = data["midcap_top5"]
                st.session_state["smallcap_top5"] = data["smallcap_top5"]
                st.session_state["analysis_timestamp"] = data["timestamp"]
                st.session_state["chat_history"] = []
                try:
                    from aibot.llm.chat import create_chat_context
                    st.session_state["chat_context"] = create_chat_context(
                        data["midcap_top5"], data["smallcap_top5"]
                    )
                except Exception:
                    st.session_state["chat_context"] = None
                st.rerun()
            else:
                st.error("Failed to load selected run.")


def _show_instructions():
    st.markdown(f"""
    <div style="background:var(--bg-secondary); border:1px solid var(--border); border-radius:10px; padding:28px; margin-top:12px;">
        <div style="font-family:'JetBrains Mono',monospace; font-size:1rem; font-weight:600;
                    color:{gc('green')}; letter-spacing:1px; margin-bottom:16px;">
            GETTING STARTED
        </div>
        <div style="color:var(--text-secondary); line-height:1.8; font-size:0.88rem;">
            <b>1. Configure API Key</b> &mdash; Edit <code>.env</code> with your Anthropic or OpenAI API key<br>
            <b>2. Click Run Analysis</b> &mdash; Scans ~400 NSE stocks (Midcap 150 + Smallcap 250)<br>
            <b>3. Explore Results</b> &mdash; Scoreboard, detailed breakdowns, and AI chat<br>
        </div>
        <div style="margin-top:16px; padding:12px; background:var(--bg-tertiary); border-radius:6px;
                    font-family:'JetBrains Mono',monospace; font-size:0.78rem; color:var(--text-secondary);">
            $ python main.py &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; # Full analysis<br>
            $ python main.py --skip-sentiment &nbsp;# Faster (no FinBERT)<br>
            $ streamlit run app.py &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# This dashboard
        </div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# SECTION 7: MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def main():
    st.markdown(generate_css(), unsafe_allow_html=True)

    # Auto-load last analysis on first visit
    if "midcap_top5" not in st.session_state and "_history_checked" not in st.session_state:
        st.session_state["_history_checked"] = True
        _try_load_latest()

    # ─── Sidebar ───
    with st.sidebar:
        sc1, sc2 = st.columns([3, 1])
        with sc1:
            st.markdown("""
            <div style="font-family:'JetBrains Mono'; font-weight:700; color:#00d4aa;
                        font-size:1.1rem; letter-spacing:3px; text-shadow:0 0 15px rgba(0,212,170,0.3);">
                AIBOT
            </div>
            """, unsafe_allow_html=True)
        with sc2:
            icon = "Light" if get_theme() == "dark" else "Dark"
            if st.button(icon, key="theme_toggle", help="Switch theme"):
                toggle_theme()
                st.rerun()

        st.divider()

        if st.button("Run Analysis", type="primary", width="stretch"):
            _run_analysis()

        skip_sentiment = st.checkbox("Skip Sentiment (faster)", value=False)
        st.session_state["skip_sentiment"] = skip_sentiment

        st.divider()
        st.markdown('<div style="font-size:0.75rem; color:var(--text-muted); letter-spacing:1px; margin-bottom:8px; font-family:\'JetBrains Mono\',monospace;">HISTORY</div>', unsafe_allow_html=True)
        _render_history_selector()

        st.divider()
        st.markdown('<div style="font-size:0.75rem; color:var(--text-muted); letter-spacing:1px; margin-bottom:8px; font-family:\'JetBrains Mono\',monospace;">SCORING WEIGHTS</div>', unsafe_allow_html=True)
        from config import WEIGHTS
        st.slider("Trend Strength", 0.0, 0.5, WEIGHTS["trend"], 0.05)
        st.slider("Volume Expansion", 0.0, 0.5, WEIGHTS["volume"], 0.05)
        st.slider("Momentum (RSI/MACD)", 0.0, 0.5, WEIGHTS["momentum"], 0.05)
        st.slider("Volatility (ATR)", 0.0, 0.3, WEIGHTS["volatility"], 0.05)
        st.slider("Delivery %", 0.0, 0.3, WEIGHTS["delivery"], 0.05)
        st.slider("Sentiment", 0.0, 0.3, WEIGHTS["sentiment"], 0.05)
        st.slider("Sector Momentum", 0.0, 0.2, WEIGHTS["sector"], 0.05)

    # ─── Header ───
    _render_header()

    # ─── Main Content ───
    if "midcap_top5" not in st.session_state:
        st.info("Click **Run Analysis** in the sidebar to start the swing trading scan.")
        _show_instructions()
        return

    midcap = st.session_state["midcap_top5"]
    smallcap = st.session_state["smallcap_top5"]

    tab1, tab2, tab3 = st.tabs(["SCOREBOARD", "STOCK DETAIL", "CHAT WITH AIBOT"])

    with tab1:
        _render_scoreboard(midcap, smallcap)
    with tab2:
        _render_detail_view(midcap, smallcap)
    with tab3:
        _render_chat()


if __name__ == "__main__":
    main()

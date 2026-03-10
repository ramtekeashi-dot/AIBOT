# AIBOT - AI Trading Analyst for NSE Swing Trading

Multi-factor scoring system that identifies the **Top 5 Midcap** and **Top 5 Smallcap** NSE stocks suitable for swing trading using technical analysis, sentiment analysis, and LLM-powered insights.

## Architecture

```
main.py                  CLI pipeline orchestrator
app.py                   Streamlit dashboard (scoreboard + detail + chat)
config.py                Scoring weights, filter thresholds, technical params

aibot/
├── data/
│   ├── universe.py      Nifty Midcap 150 + Smallcap 250 constituents
│   ├── price_data.py    OHLCV batch download via yfinance
│   ├── delivery_data.py Delivery % from NSE API
│   └── fii_dii.py       FII/DII institutional activity
├── analysis/
│   ├── technical.py     RSI, MACD, ATR, EMA trends, volume expansion
│   ├── sentiment.py     Google News RSS + FinBERT sentiment classification
│   └── sector_momentum.py  Sector-level 10D return calculation
├── scoring/
│   ├── filters.py       Hard exclusion rules (RSI>75, delivery<10%, etc.)
│   ├── normalizer.py    Domain-aware normalization to 0-100 scale
│   └── scorer.py        Weighted composite Swing Score + ranking
├── llm/
│   ├── rationale.py     Claude/GPT trading rationale generation
│   └── chat.py          Conversational Q&A over analysis results
└── output/
    ├── levels.py        Support/Resistance (pivot points + peak detection)
    └── report.py        CLI text report + CSV export
```

## Pipeline Flow

1. **Universe Construction** — Fetch Nifty Midcap 150 + Smallcap 250 constituents
2. **Data Download** — Batch OHLCV data via yfinance (~400 stocks)
3. **FII/DII Activity** — Institutional cash market data from NSE
4. **Sector Momentum** — Average 10-day return per sector
5. **Stock Analysis** — For each stock (parallelized):
   - Technical indicators (RSI, MACD, ATR, EMA alignment, volume expansion)
   - Delivery % from NSE
   - News sentiment via FinBERT
6. **Filtering & Scoring** — Hard filters → normalize → weighted composite score
7. **S/R Levels** — Support/resistance via pivot points + scipy peak detection
8. **LLM Rationales** — AI-generated 2-3 line trading insights per stock

## Scoring Model (Swing Score 0-100)

| Component            | Weight |
|----------------------|--------|
| Trend Strength       | 25%    |
| Volume Expansion     | 20%    |
| Momentum (RSI/MACD)  | 20%    |
| Volatility (ATR%)    | 10%    |
| Delivery %           | 10%    |
| News Sentiment       | 10%    |
| Sector Momentum      | 5%     |

## Hard Filters

Stocks are excluded if any condition is met:
- RSI > 75 (overbought)
- Delivery < 10%
- Negative news sentiment
- ATR% > 6% (too volatile)
- Price < INR 50

## Quick Start

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure API Key (for LLM features)

Edit `.env`:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6
```

### Run CLI

```bash
python main.py                    # Full analysis with FinBERT sentiment
python main.py --skip-sentiment   # Skip sentiment (faster, ~2 min)
python main.py --no-csv           # Skip CSV export
```

### Run Streamlit Dashboard

```bash
streamlit run app.py
```

Dashboard features:
- **Scoreboard** — Top 5 midcap + smallcap ranked cards with scores
- **Stock Detail** — Component score breakdown, technicals, S/R levels, sentiment
- **Chat** — Ask questions about the analysis powered by Claude/GPT

## Tech Stack

| Library       | Purpose                                    |
|---------------|--------------------------------------------|
| yfinance      | OHLCV price data (batch download)          |
| pandas-ta     | RSI, MACD, ATR (pure Python, no TA-Lib)   |
| niftystocks   | Index constituent lists                    |
| transformers  | FinBERT financial sentiment analysis       |
| scipy         | Support/resistance peak detection          |
| anthropic     | Claude API for rationale + chat            |
| streamlit     | Interactive web dashboard                  |
| plotly        | Candlestick charts + score visualizations  |

## Output

Each top pick includes:
- Swing Score (0-100)
- Price trend (5D / 10D / 20D)
- Volume expansion %
- RSI, MACD status
- ATR%
- Delivery %
- News sentiment (positive/neutral/negative)
- Support and resistance levels
- AI-generated 2-3 line swing trading rationale

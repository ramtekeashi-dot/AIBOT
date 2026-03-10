"""Central configuration for AIBOT Trading Analyst."""

# ─── Scoring Weights (must sum to 1.0) ───
WEIGHTS = {
    "trend": 0.25,
    "volume": 0.20,
    "momentum": 0.20,
    "volatility": 0.10,
    "delivery": 0.10,
    "sentiment": 0.10,
    "sector": 0.05,
}

# ─── Hard Filter Thresholds ───
RSI_MAX = 75          # Exclude overbought
DELIVERY_MIN = 10     # Minimum delivery %
ATR_PCT_MAX = 6.0     # Max volatility %
PRICE_MIN = 50        # Min price INR

# ─── Technical Indicator Parameters ───
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
ATR_PERIOD = 14

# ─── Lookback Windows ───
TREND_5D = 5
TREND_10D = 10
TREND_20D = 20
VOLUME_SHORT = 5
VOLUME_LONG = 20
SECTOR_LOOKBACK = 10

# ─── Data Fetch Settings ───
OHLCV_PERIOD = "3mo"       # yfinance period for historical data
MAX_WORKERS = 10            # ThreadPoolExecutor parallelism
TOP_N = 5                   # Top N picks per category

# ─── Sentiment Settings ───
FINBERT_MODEL = "ProsusAI/finbert"
MAX_NEWS_HEADLINES = 5

# ─── LLM Settings ───
LLM_MAX_TOKENS = 300
LLM_TEMPERATURE = 0.3

# ─── Sector Mapping (NSE symbol → sector) ───
# Auto-populated at runtime via yfinance .info["sector"]
# Fallback mapping for common stocks
SECTOR_FALLBACK = {
    "IT": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM", "LTIM", "MPHASIS", "COFORGE", "PERSISTENT", "LTTS"],
    "Banking": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK", "BANKBARODA", "PNB", "INDUSINDBK", "FEDERALBNK", "IDFCFIRSTB"],
    "Pharma": ["SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "AUROPHARMA", "LUPIN", "BIOCON", "TORNTPHARM", "ALKEM", "IPCALAB"],
    "Auto": ["MARUTI", "TATAMOTORS", "M&M", "BAJAJ-AUTO", "HEROMOTOCO", "EICHERMOT", "ASHOKLEY", "TVSMOTOR", "BHARATFORG", "MOTHERSON"],
    "FMCG": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "DABUR", "MARICO", "GODREJCP", "COLPAL", "TATACONSUM", "VBL"],
    "Metal": ["TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL", "COALINDIA", "NMDC", "NATIONALUM", "JINDALSTEL", "SAIL", "APLAPOLLO"],
    "Energy": ["RELIANCE", "ONGC", "BPCL", "IOC", "GAIL", "NTPC", "POWERGRID", "ADANIGREEN", "TATAPOWER", "NHPC"],
    "Realty": ["DLF", "GODREJPROP", "OBEROIRLTY", "PRESTIGE", "PHOENIXLTD", "BRIGADE", "SOBHA", "SUNTECK"],
    "Infra": ["LARSEN", "ADANIENT", "ADANIPORTS", "ULTRACEMCO", "GRASIM", "ACC", "AMBUJACEM", "SHREECEM"],
    "Finance": ["BAJFINANCE", "BAJAJFINSV", "SBILIFE", "HDFCLIFE", "ICICIPRULI", "MUTHOOTFIN", "MANAPPURAM", "CHOLAFIN", "SHRIRAMFIN"],
}

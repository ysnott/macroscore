import streamlit as st
import requests
import datetime
import os

# ====== CONFIG ======
API_KEY = os.getenv("TWELVE_DATA_API_KEY", "fd361e714c704855964af24234085bc6")
BASE_URL = "https://api.twelvedata.com"
FOREX_PAIRS = [
    "EUR/USD", "AUD/USD", "NZD/USD", "USD/JPY", "USD/CAD", "GBP/USD", "USD/CHF", "EUR/GBP"
]
SIGNAL_WINDOW = 10  # minutes for momentum signal

# ====== DATA FETCHING ======
def fetch_price_history(pair, window=SIGNAL_WINDOW):
    url = f"{BASE_URL}/time_series?symbol={pair}&interval=1min&apikey={API_KEY}&outputsize={window}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        if "values" in data and len(data["values"]) >= 2:
            latest = float(data["values"][0]["close"])
            oldest = float(data["values"][-1]["close"])
            change = latest - oldest
            return latest, oldest, change
        elif "values" in data and len(data["values"]) == 1:
            return float(data["values"][0]["close"]), None, None
        return None, None, None
    except Exception as e:
        return None, None, None

def fetch_dxy():
    url = f"{BASE_URL}/time_series?symbol=DXY&interval=1min&apikey={API_KEY}&outputsize=1"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        if "values" in data and len(data["values"]) >= 1:
            return float(data["values"][0]["close"])
        return None
    except Exception:
        return None

# ====== SIGNALS & ANALYSIS ======
def get_signal(latest, oldest):
    if latest is None or oldest is None:
        return "❓ N/A"
    if abs(latest - oldest) < 0.00005:
        return "⚪ Neutral"
    if latest > oldest:
        return "🟢 Bullish"
    else:
        return "🔴 Bearish"

def get_macro_placeholder():
    # Placeholder for macro data, ready for future API integration
    return {
        "Inflation Rate (YoY %)": None,
        "Unemployment Rate": None,
        "Interest Rate": None,
        "GDP Growth Rate": None
    }

# ====== STREAMLIT UI ======
st.set_page_config(page_title="MacroScore Dashboard", layout="wide")
st.title("📊 MacroScore Real-Time Dashboard with Forex Pairs")
st.markdown("**All data live from Twelve Data API**")

# --- MACRO SECTION (placeholder, can be replaced with real API integration) ---
st.subheader("📈 Latest Macroeconomic Indicators")
macro = get_macro_placeholder()
cols = st.columns(5)
for i, key in enumerate(list(macro.keys()) + ["USD Index (DXY)"]):
    if key == "USD Index (DXY)":
        with st.spinner("Fetching DXY..."):
            dxy_price = fetch_dxy()
        val = f"{dxy_price:.2f}" if dxy_price is not None else "N/A"
        cols[i].metric(key, val)
    else:
        cols[i].metric(key, "N/A")
if all(v is None for v in macro.values()):
    st.info("Twelve Data does not provide macroeconomic indicators. For macro data, consider integrating FRED or Trading Economics API.")

# --- MARKET SENTIMENT (placeholder, can be dynamic if macro is integrated) ---
st.subheader("📉 Market Sentiment Based on Macro Score")
st.markdown("### 🔴 **Strong Bearish** (Macro signals not available)")

# --- FOREX TABLE WITH SIGNALS ---
st.subheader("💱 Forex Pairs Rates & Signals")
with st.spinner("Fetching live Forex rates and signals..."):
    forex_rows = []
    for pair in FOREX_PAIRS:
        latest, oldest, change = fetch_price_history(pair)
        signal = get_signal(latest, oldest)
        rate_str = f"{latest:.5f}" if latest is not None else "N/A"
        forex_rows.append((pair, rate_str, signal))

    # Table
    st.table(
        [{"Pair": pair, "Rate": rate, "Signal": signal} for pair, rate, signal in forex_rows]
    )

# --- FUTURE: Charts, statistics, history, technical analysis ---
st.markdown("""
**Planned improvements:**
- Integrate real macro indicators (FRED, Trading Economics API)
- Add charts for Forex pairs
- Display historical performance and volatility
- Technical analysis signals (RSI, MACD, etc.)
- Multi-API support and configuration
""")

st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("👨‍💻 Created by YSNOTT")

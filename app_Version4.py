import streamlit as st
import requests
import datetime
import os

API_KEY = os.getenv("TWELVE_DATA_API_KEY", "fd361e714c704855964af24234085bc6")
BASE_URL = "https://api.twelvedata.com"
FOREX_PAIRS = [
    "EUR/USD", "AUD/USD", "NZD/USD", "USD/JPY", "USD/CAD", "GBP/USD", "USD/CHF", "EUR/GBP"
]

def fetch_price_history(pair):
    url = f"{BASE_URL}/time_series?symbol={pair}&interval=1min&apikey={API_KEY}&outputsize=10"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        if "values" in data and len(data["values"]) >= 2:
            latest = float(data["values"][0]["close"])
            oldest = float(data["values"][-1]["close"])
            return latest, oldest
        elif "values" in data and len(data["values"]) == 1:
            return float(data["values"][0]["close"]), None
        return None, None
    except Exception as e:
        st.warning(f"Error fetching {pair}: {e}")
        return None, None

def get_signal(latest, oldest):
    if latest is None or oldest is None:
        return "❓ N/A"
    if abs(latest - oldest) < 0.00005:
        return "⚪ Neutral"
    if latest > oldest:
        return "🟢 Bullish"
    else:
        return "🔴 Bearish"

def fetch_dxy():
    url = f"{BASE_URL}/time_series?symbol=DXY&interval=1min&apikey={API_KEY}&outputsize=1"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        if "values" in data and len(data["values"]) >= 1:
            return float(data["values"][0]["close"])
        return None
    except Exception as e:
        st.warning("DXY not available in your plan or missing from Twelve Data.")
        return None

st.set_page_config(page_title="MacroScore Dashboard", layout="wide")
st.title("📊 MacroScore Real-Time Dashboard with Forex Pairs")
st.markdown("**All data live from Twelve Data API**")

st.subheader("📈 Latest Macroeconomic Indicators")
cols = st.columns(5)
cols[0].metric("Inflation Rate (YoY %)", "N/A")
cols[1].metric("Unemployment Rate", "N/A")
cols[2].metric("Interest Rate", "N/A")
cols[3].metric("GDP Growth Rate", "N/A")
with st.spinner("Fetching DXY..."):
    dxy_price = fetch_dxy()
dxy_val = f"{dxy_price:.2f}" if dxy_price is not None else "N/A"
cols[4].metric("USD Index (DXY)", dxy_val)
if dxy_price is None:
    st.info("Twelve Data does not provide macroeconomic indicators. For macro data, use FRED or Trading Economics.")

st.subheader("📉 Market Sentiment Based on Macro Score")
st.markdown("### 🔴 **Strong Bearish** (Macro signals not available)")

st.subheader("💱 Forex Pairs Rates & Signals")
with st.spinner("Fetching live Forex rates and signals..."):
    for pair in FOREX_PAIRS:
        latest, oldest = fetch_price_history(pair)
        signal = get_signal(latest, oldest)
        if latest is not None:
            st.write(f"**{pair}**: {latest:.5f} — {signal}")
        else:
            st.write(f"**{pair}**: N/A — {signal}")

st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("👨‍💻 Created by YSNOTT")

import streamlit as st
import requests
import datetime
import os

API_KEY = os.getenv("TWELVE_DATA_API_KEY", "fd361e714c704855964af24234085bc6")
BASE_URL = "https://api.twelvedata.com"
FOREX_PAIRS = [
    "EUR/USD", "AUD/USD", "NZD/USD", "USD/JPY", "USD/CAD", "GBP/USD", "USD/CHF", "EUR/GBP"
]

def fetch_latest_price(pair):
    url = f"{BASE_URL}/time_series?symbol={pair}&interval=1min&apikey={API_KEY}&outputsize=2"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        if "values" in data and len(data["values"]) >= 2:
            current = float(data["values"][0]["close"])
            previous = float(data["values"][1]["close"])
            return current, previous
        elif "values" in data and len(data["values"]) == 1:
            return float(data["values"][0]["close"]), None
        return None, None
    except Exception as e:
        st.warning(f"Error fetching {pair}: {e}")
        return None, None

def get_signal(current, previous):
    if current is None or previous is None:
        return "❓ N/A"
    change = current - previous
    if abs(change) < 0.0001:  # very flat, could be a tight spread
        return "⚪ Neutral"
    elif change > 0:
        return "🟢 Bullish"
    else:
        return "🔴 Bearish"

st.set_page_config(page_title="MacroScore Dashboard", layout="wide")
st.title("📊 MacroScore Real-Time Dashboard with Forex Pairs")
st.markdown("**All data live from Twelve Data API**")

# Macro indicators not available via Twelve Data, set N/A
cols = st.columns(5)
cols[0].metric("Inflation Rate (YoY %)", "N/A")
cols[1].metric("Unemployment Rate", "N/A")
cols[2].metric("Interest Rate", "N/A")
cols[3].metric("GDP Growth Rate", "N/A")
with st.spinner("Fetching DXY..."):
    # DXY may not exist in your plan, so fallback to N/A
    dxy_price, _ = fetch_latest_price("DXY")
cols[4].metric("USD Index (DXY)", f"{dxy_price:.2f}" if dxy_price is not None else "N/A")

# Since macro indicators are N/A, sentiment will always be "Strong Bearish"
sentiment = "Strong Bearish"
sentiment_color = "🔴"
st.subheader("📉 Market Sentiment Based on Macro Score")
st.markdown(f"### {sentiment_color} **{sentiment}**")

st.subheader("💱 Forex Pairs Rates & Signals")
with st.spinner("Fetching live Forex rates and signals..."):
    for pair in FOREX_PAIRS:
        current, previous = fetch_latest_price(pair)
        signal = get_signal(current, previous)
        if current is not None:
            st.write(f"**{pair}**: {current:.5f} — {signal}")
        else:
            st.write(f"**{pair}**: N/A — {signal}")

st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("👨‍💻 Created by YSNOTT")

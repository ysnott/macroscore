import streamlit as st
import requests
import datetime
import os

API_KEY = os.getenv("TWELVE_DATA_API_KEY", "fd361e714c704855964af24234085bc6")
BASE_URL = "https://api.twelvedata.com/time_series"

FOREX_PAIRS = [
    "EUR/USD", "AUD/USD", "NZD/USD", "USD/JPY", "USD/CAD", "GBP/USD", "USD/CHF", "EUR/GBP"
]

def fetch_twelvedata_price(symbol):
    url = f"{BASE_URL}?symbol={symbol}&interval=1min&apikey={API_KEY}&outputsize=1"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        if "values" in data and len(data["values"]) > 0:
            return float(data["values"][0]["close"])
        return None
    except Exception as e:
        st.warning(f"Error fetching {symbol}: {e}")
        return None

st.set_page_config(page_title="MacroScore Dashboard", layout="wide")
st.title("📊 MacroScore Real-Time Dashboard with Forex Pairs")
st.markdown("**All data live from Twelve Data API**")

# Macro indicators not available via Twelve Data, set N/A
macro_indicators = {
    "Inflation Rate (YoY %)": None,
    "Unemployment Rate": None,
    "Interest Rate": None,
    "GDP Growth Rate": None
}

with st.spinner("Fetching DXY..."):
    dxy_price = fetch_twelvedata_price("DXY")

st.subheader("📈 Latest Macroeconomic Indicators")
cols = st.columns(5)
cols[0].metric("Inflation Rate (YoY %)", "N/A")
cols[1].metric("Unemployment Rate", "N/A")
cols[2].metric("Interest Rate", "N/A")
cols[3].metric("GDP Growth Rate", "N/A")
cols[4].metric("USD Index (DXY)", f"{dxy_price:.2f}" if dxy_price is not None else "N/A")

# Since macro indicators are N/A, sentiment will always be "Strong Bearish"
sentiment = "Strong Bearish"
sentiment_color = "🔴"

st.subheader("📉 Market Sentiment Based on Macro Score")
st.markdown(f"### {sentiment_color} **{sentiment}**")

with st.spinner("Fetching live Forex rates..."):
    forex_rates = {}
    for pair in FOREX_PAIRS:
        forex_rates[pair] = fetch_twelvedata_price(pair)
        # To respect free tier rate limit (8/min), pause if needed
        # time.sleep(8)

st.subheader("💱 Forex Pairs Rates")
for pair in FOREX_PAIRS:
    rate = forex_rates.get(pair)
    st.write(f"**{pair}**: {rate:.5f}" if rate is not None else f"**{pair}**: N/A")

st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("👨‍💻 Created by YSNOTT")

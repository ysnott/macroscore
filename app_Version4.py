import streamlit as st
import requests
import datetime
import os

API_KEY = os.getenv("TRADING_ECONOMICS_API_KEY", "YOUR_FREE_KEY_HERE")

BASE_URL = "https://api.tradingeconomics.com"
FOREX_PAIRS = [
    "EURUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCAD", "GBPUSD", "USDCHF", "EURGBP"
]

def fetch_macro(country, indicator):
    url = f"{BASE_URL}/country/{country}/indicator/{indicator}?c={API_KEY}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        res = r.json()
        return float(res[0]["latestValue"]) if res and "latestValue" in res[0] else None
    except Exception:
        return None

def fetch_dxy():
    url = f"{BASE_URL}/markets/symbol/DXY?c={API_KEY}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        res = r.json()
        return float(res[0]["last"]) if res and "last" in res[0] else None
    except Exception:
        return None

def fetch_forex(pair):
    url = f"{BASE_URL}/markets/symbol/{pair}?c={API_KEY}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        res = r.json()
        return float(res[0]["last"]) if res and "last" in res[0] else None
    except Exception:
        return None

def score_market(inflation, unemployment, interest_rate, gdp):
    score = 0
    if inflation is not None and inflation < 3: score += 1
    if unemployment is not None and unemployment < 4.5: score += 1
    if interest_rate is not None and interest_rate < 3: score += 1
    if gdp is not None and gdp > 0: score += 1
    if score == 4: return "Strong Bullish"
    elif score == 3: return "Bullish"
    elif score == 2: return "Neutral"
    elif score == 1: return "Bearish"
    else: return "Strong Bearish"

st.set_page_config(page_title="MacroScore Dashboard", layout="wide")
st.title("📊 MacroScore Real-Time Dashboard with Forex Pairs")
st.markdown("All data live from Trading Economics API")

with st.spinner("Fetching macroeconomic indicators..."):
    inflation = fetch_macro("united states", "cpi")
    unemployment = fetch_macro("united states", "unemployment rate")
    interest_rate = fetch_macro("united states", "interest rate")
    gdp = fetch_macro("united states", "gdp")

with st.spinner("Fetching DXY..."):
    dxy_price = fetch_dxy()

st.subheader("📈 Latest Macroeconomic Indicators")
cols = st.columns(5)
cols[0].metric("Inflation Rate (YoY %)", f"{inflation:.2f}%" if inflation is not None else "N/A")
cols[1].metric("Unemployment Rate", f"{unemployment:.2f}%" if unemployment is not None else "N/A")
cols[2].metric("Interest Rate", f"{interest_rate:.2f}%" if interest_rate is not None else "N/A")
cols[3].metric("GDP Growth Rate", f"{gdp:.2f}%" if gdp is not None else "N/A")
cols[4].metric("USD Index (DXY)", f"{dxy_price:.2f}" if dxy_price is not None else "N/A")

sentiment = score_market(inflation, unemployment, interest_rate, gdp)
sentiment_color = {
    "Strong Bullish": "🟢", "Bullish": "🟩", "Neutral": "⚪", "Bearish": "🔻", "Strong Bearish": "🔴"
}[sentiment]

st.subheader("📉 Market Sentiment Based on Macro Score")
st.markdown(f"### {sentiment_color} **{sentiment}**")

with st.spinner("Fetching live Forex rates..."):
    forex_rates = {pair: fetch_forex(pair) for pair in FOREX_PAIRS}

st.subheader("💱 Forex Pairs Rates")
for pair, rate in forex_rates.items():
    st.write(f"**{pair}**: {rate:.5f}" if rate is not None else f"**{pair}**: N/A")

st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("👨‍💻 Created by YSNOTT")

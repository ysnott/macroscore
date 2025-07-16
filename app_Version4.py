import streamlit as st
import requests
import datetime
import os

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "NGUEM2H25VEWLK3U")

def fetch_forex_rate(pair):
    from_symbol, to_symbol = pair.split('/')
    url = f"https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol={from_symbol}&to_symbol={to_symbol}&interval=5min&apikey={API_KEY}"
    r = requests.get(url)
    data = r.json()
    try:
        latest = next(iter(data['Time Series FX (5min)'].values()))
        return float(latest['4. close'])
    except Exception:
        return None

def fetch_dxy():
    # DXY not directly available from Alpha Vantage, but can estimate via USD pairs or use ETF price.
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=UUP&apikey={API_KEY}"
    r = requests.get(url)
    data = r.json()
    try:
        return float(data["Global Quote"]["05. price"])
    except Exception:
        return None

def fetch_macro(function, symbol=None):
    if symbol:
        url = f"https://www.alphavantage.co/query?function={function}&symbol={symbol}&apikey={API_KEY}"
    else:
        url = f"https://www.alphavantage.co/query?function={function}&apikey={API_KEY}"
    r = requests.get(url)
    data = r.json()
    # For GDP, CPI, Unemployment, Interest Rate
    try:
        if function == "REAL_GDP":
            val = data["data"][0]["value"]
        elif function == "CPI":
            val = data["data"][0]["value"]
        elif function == "UNEMPLOYMENT":
            val = data["data"][0]["value"]
        elif function == "FEDERAL_FUNDS_RATE":
            val = data["data"][0]["value"]
        else:
            val = None
        return float(val)
    except Exception:
        return None

FOREX_PAIRS = [
    "EUR/USD", "AUD/USD", "NZD/USD", "USD/JPY", "USD/CAD", "GBP/USD", "USD/CHF", "EUR/GBP"
]

st.set_page_config(page_title="MacroScore Dashboard", layout="wide")
st.title("📊 MacroScore Real-Time Dashboard with Forex Pairs")
st.markdown("All data live from Alpha Vantage API")

with st.spinner("Fetching macroeconomic indicators..."):
    inflation = fetch_macro("CPI")
    unemployment = fetch_macro("UNEMPLOYMENT")
    interest_rate = fetch_macro("FEDERAL_FUNDS_RATE")
    gdp = fetch_macro("REAL_GDP")

with st.spinner("Fetching DXY..."):
    dxy_price = fetch_dxy()

st.subheader("📈 Latest Macroeconomic Indicators")
cols = st.columns(5)
cols[0].metric("Inflation Rate (YoY %)", f"{inflation:.2f}%" if inflation is not None else "N/A")
cols[1].metric("Unemployment Rate", f"{unemployment:.2f}%" if unemployment is not None else "N/A")
cols[2].metric("Interest Rate", f"{interest_rate:.2f}%" if interest_rate is not None else "N/A")
cols[3].metric("GDP Growth Rate", f"{gdp:.2f}%" if gdp is not None else "N/A")
cols[4].metric("USD Index (DXY)", f"{dxy_price:.2f}" if dxy_price is not None else "N/A")

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

sentiment = score_market(inflation, unemployment, interest_rate, gdp)
sentiment_color = {
    "Strong Bullish": "🟢", "Bullish": "🟩", "Neutral": "⚪", "Bearish": "🔻", "Strong Bearish": "🔴"
}[sentiment]

st.subheader("📉 Market Sentiment Based on Macro Score")
st.markdown(f"### {sentiment_color} **{sentiment}**")

with st.spinner("Fetching live Forex rates..."):
    forex_rates = {pair: fetch_forex_rate(pair) for pair in FOREX_PAIRS}

st.subheader("💱 Forex Pairs Rates")
for pair, rate in forex_rates.items():
    st.write(f"**{pair}**: {rate:.5f}" if rate is not None else f"**{pair}**: N/A")

st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("👨‍💻 Created by YSNOTT")

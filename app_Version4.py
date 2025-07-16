import os
import time
import streamlit as st
import requests
import datetime

# --- API KEYS & URLS ---
FRED_API_KEY = os.getenv("FRED_API_KEY", "e072fbb3098e26e777214caac7c036d3")  # Replace with your FRED API Key
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "fd361e714c704855964af24234085bc6")  # Replace with your Twelve Data API Key

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
TWELVE_DATA_BASE_URL = "https://api.twelvedata.com/time_series"

# --- Macro Indicators & Pairs ---
INDICATORS = {
    "Inflation Rate (YoY %)": "CPIAUCSL",
    "Unemployment Rate": "UNRATE",
    "Federal Funds Rate": "FEDFUNDS",
    "GDP Growth Rate": "A191RL1Q225SBEA",
}

FOREX_PAIRS = [
    "EUR/USD", "AUD/USD", "NZD/USD", "EUR/CAD", "AUD/JPY", "NZD/JPY",
    "AUD/CAD", "NZD/CAD", "USD/JPY"
]

# --- Functions ---
def get_fred_data(series_id):
    """
    Fetch data for a given FRED series ID.
    """
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "limit": 500,
    }
    try:
        response = requests.get(FRED_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        observations = data.get("observations", [])
        valid_obs = [obs for obs in observations if obs.get("value") not in (".", "")]
        return float(valid_obs[-1]["value"]) if valid_obs else None
    except Exception as e:
        st.error(f"Error fetching data for {series_id}: {e}")
        return None


def fetch_forex_rates(pairs):
    """
    Fetch live Forex rates in batches to respect API rate limits.
    """
    rates = {}
    for i, pair in enumerate(pairs):
        if i > 0 and i % 8 == 0:  # Respect API rate limit by pausing after every 8 requests
            time.sleep(60)
        
        try:
            url = f"{TWELVE_DATA_BASE_URL}?symbol={pair}&interval=1min&apikey={TWELVE_DATA_API_KEY}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if "values" in data:
                latest = data["values"][0]  # Get the latest data point
                rate = float(latest["close"])  # Use the close price as the rate
                rates[pair] = rate
            else:
                rates[pair] = None
        except Exception as e:
            st.error(f"Error fetching Forex rate for {pair}: {e}")
            rates[pair] = None
    return rates


def fetch_dxy_price():
    """
    Fetch real-time DXY price using Twelve Data API.
    """
    try:
        url = f"{TWELVE_DATA_BASE_URL}?symbol=DXY&interval=1min&apikey={TWELVE_DATA_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if "values" in data:
            latest = data["values"][0]  # Get the latest data point
            price = float(latest["close"])  # Use the close price
            return price
        else:
            st.error(f"Error fetching DXY price: {data.get('message', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Error fetching DXY price: {e}")
        return None


def score_market(inflation, unemployment, interest_rate, gdp):
    """
    Score the market based on macroeconomic indicators.
    """
    score = 0
    if inflation is not None and inflation < 3: score += 1
    if unemployment is not None and unemployment < 4.5: score += 1
    if interest_rate is not None and interest_rate < 3: score += 1
    if gdp is not None and gdp > 0: score += 1

    if score == 4:
        return "Strong Bullish"
    elif score >= 3:
        return "Bullish"
    elif score == 2:
        return "Neutral"
    elif score == 1:
        return "Bearish"
    else:
        return "Strong Bearish"

# --- Streamlit App ---
st.set_page_config(page_title="MacroScore Dashboard with Twelve Data", layout="wide")
st.title("📊 MacroScore Real-Time Dashboard with Forex Pairs")
st.markdown("Real-time macroeconomic indicators from FRED + live Forex rates + live DXY from Twelve Data")

with st.spinner("Fetching macroeconomic data..."):
    inflation = get_fred_data(INDICATORS["Inflation Rate (YoY %)"])
    unemployment = get_fred_data(INDICATORS["Unemployment Rate"])
    interest_rate = get_fred_data(INDICATORS["Federal Funds Rate"])
    gdp = get_fred_data(INDICATORS["GDP Growth Rate"])

with st.spinner("Fetching DXY price..."):
    dxy_price = fetch_dxy_price()

st.subheader("📈 Latest Macroeconomic Indicators")
cols = st.columns(5)
cols[0].metric("Inflation Rate (YoY %)", f"{inflation:.2f}%" if inflation is not None else "N/A")
cols[1].metric("Unemployment Rate", f"{unemployment:.2f}%" if unemployment is not None else "N/A")
cols[2].metric("Interest Rate", f"{interest_rate:.2f}%" if interest_rate is not None else "N/A")
cols[3].metric("GDP Growth Rate", f"{gdp:.2f}%" if gdp is not None else "N/A")
cols[4].metric("USD Index (Real-Time DXY)", f"{dxy_price:.2f}" if dxy_price is not None else "N/A")

sentiment = score_market(inflation, unemployment, interest_rate, gdp)
sentiment_color = {
    "Strong Bullish": "🟢",
    "Bullish": "🟩",
    "Neutral": "⚪",
    "Bearish": "🔻",
    "Strong Bearish": "🔴"
}.get(sentiment, "❓")

st.subheader("📉 Market Sentiment Based on Macro Score")
st.markdown(f"### {sentiment_color} **{sentiment}**")

with st.spinner("Fetching live Forex rates..."):
    forex_rates = fetch_forex_rates(FOREX_PAIRS)

st.subheader("💱 Forex Pairs Rates")
for pair, rate in forex_rates.items():
    st.write(f"**{pair}**: {rate:.5f}" if rate else "N/A")

st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("👨‍💻 Created by YSNOTT")

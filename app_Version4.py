import os
import time
import streamlit as st
import requests
import datetime

# --- API KEYS & URLS ---
FRED_API_KEY = os.getenv("FRED_API_KEY", "e072fbb3098e26e777214caac7c036d3")
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "fd361e714c704855964af24234085bc6")
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
    "EUR/USD", "AUD/USD", "NZD/USD", "USD/JPY", "USD/CAD", "GBP/USD", "USD/CHF", "EUR/GBP"
]  # limit to 8 pairs for free tier

# --- Functions ---
def get_fred_data(series_id):
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
        observations = [obs for obs in data.get("observations", []) if obs.get("value") not in (".", "")]
        return observations
    except Exception as e:
        st.error(f"Error fetching data for {series_id}: {e}")
        return []

def calculate_cpi_yoy(observations):
    # Find latest and value from same month last year
    if len(observations) < 13:
        return None
    latest = float(observations[-1]["value"])
    latest_date = observations[-1]["date"]
    # Find previous year same month
    for obs in reversed(observations):
        if obs["date"][:4] == str(int(latest_date[:4]) - 1) and obs["date"][5:7] == latest_date[5:7]:
            prev = float(obs["value"])
            break
    else:
        return None
    return ((latest - prev) / prev) * 100

def fetch_forex_rate(pair):
    url = f"{TWELVE_DATA_BASE_URL}?symbol={pair}&interval=1min&apikey={TWELVE_DATA_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if "values" in data:
            return float(data["values"][0]["close"])
        return None
    except Exception as e:
        st.warning(f"Error fetching Forex rate for {pair}: {e}")
        return None

def fetch_dxy_price():
    url = f"{TWELVE_DATA_BASE_URL}?symbol=DXY&interval=1min&apikey={TWELVE_DATA_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if "values" in data:
            return float(data["values"][0]["close"])
        return None
    except Exception as e:
        st.warning(f"Error fetching DXY price: {e}")
        return None

def score_market(inflation, unemployment, interest_rate, gdp):
    score = 0
    if inflation is not None and inflation < 3: score += 1
    if unemployment is not None and unemployment < 4.5: score += 1
    if interest_rate is not None and interest_rate < 3: score += 1
    if gdp is not None and gdp > 0: score += 1
    if score == 4:
        return "Strong Bullish"
    elif score == 3:
        return "Bullish"
    elif score == 2:
        return "Neutral"
    elif score == 1:
        return "Bearish"
    else:
        return "Strong Bearish"

# --- Streamlit App ---
st.set_page_config(page_title="MacroScore Dashboard", layout="wide")
st.title("📊 MacroScore Real-Time Dashboard with Forex Pairs")
st.markdown("Real-time macroeconomic indicators from FRED + live Forex rates + live DXY from Twelve Data")

with st.spinner("Fetching macroeconomic data..."):
    cpi_obs = get_fred_data(INDICATORS["Inflation Rate (YoY %)"])
    inflation = calculate_cpi_yoy(cpi_obs)
    unemployment_obs = get_fred_data(INDICATORS["Unemployment Rate"])
    unemployment = float(unemployment_obs[-1]["value"]) if unemployment_obs else None
    interest_obs = get_fred_data(INDICATORS["Federal Funds Rate"])
    interest_rate = float(interest_obs[-1]["value"]) if interest_obs else None
    gdp_obs = get_fred_data(INDICATORS["GDP Growth Rate"])
    gdp = float(gdp_obs[-1]["value"]) if gdp_obs else None

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
}[sentiment]

st.subheader("📉 Market Sentiment Based on Macro Score")
st.markdown(f"### {sentiment_color} **{sentiment}**")

with st.spinner("Fetching live Forex rates..."):
    forex_rates = {}
    for pair in FOREX_PAIRS:
        rate = fetch_forex_rate(pair)
        forex_rates[pair] = rate
        time.sleep(8)  # Wait to avoid hitting the rate limit (8 requests/minute)

st.subheader("💱 Forex Pairs Rates")
for pair, rate in forex_rates.items():
    st.write(f"**{pair}**: {rate:.5f}" if rate else "N/A")

st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("👨‍💻 Created by YSNOTT")

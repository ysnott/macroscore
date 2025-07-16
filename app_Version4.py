import streamlit as st
import requests
import datetime

# ✅ Replace with your real FRED API key
API_KEY = "your_real_api_key_here"
BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# ✅ Function to fetch data from FRED
def get_fred_data(series_id, start_date="2022-01-01"):
    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json",
        "observation_start": start_date
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        observations = data.get("observations", [])
        for obs in reversed(observations):
            if obs["value"] != ".":
                return float(obs["value"])
    except Exception as e:
        st.error(f"Error fetching data for {series_id}: {e}")
    return None

# ✅ Indicator Series IDs
INDICATORS = {
    "Inflation Rate (CPI)": "CPIAUCSL",
    "Unemployment Rate": "UNRATE",
    "Federal Funds Rate": "FEDFUNDS",
    "GDP Growth Rate": "A191RL1Q225SBEA",
    "US Dollar Index (DXY proxy)": "DTWEXAFEGS"
}

# ✅ Scoring logic
def score_market(inflation, unemployment, interest_rate, gdp, dollar_index):
    if None in [inflation, unemployment, interest_rate, gdp, dollar_index]:
        return "Insufficient Data"

    score = 0
    if inflation < 3: score += 1
    if unemployment < 4.5: score += 1
    if interest_rate < 3: score += 1
    if gdp > 2: score += 1
    if dollar_index > 110: score += 1

    if score == 5:
        return "Strong Bullish"
    elif score >= 3:
        return "Bullish"
    elif score == 2:
        return "Neutral"
    elif score == 1:
        return "Bearish"
    else:
        return "Strong Bearish"

# ✅ Streamlit UI setup
st.set_page_config(page_title="MacroScore Dashboard", layout="wide")
st.title("📊 MacroScore Real-Time Dashboard")

st.markdown("This dashboard analyzes real-time macroeconomic data and gives a sentiment score for markets based on FRED indicators.")

# ✅ Fetch macro data
with st.spinner("Fetching real-time data from FRED..."):
    inflation = get_fred_data(INDICATORS["Inflation Rate (CPI)"])
    unemployment = get_fred_data(INDICATORS["Unemployment Rate"])
    interest_rate = get_fred_data(INDICATORS["Federal Funds Rate"])
    gdp = get_fred_data(INDICATORS["GDP Growth Rate"])
    dollar_index = get_fred_data(INDICATORS["US Dollar Index (DXY proxy)"])

# ✅ Show indicators
st.subheader("📈 Latest Macroeconomic Indicators")
cols = st.columns(5)
cols[0].metric("Inflation Rate (CPI)", f"{inflation if inflation is not None else 'N/A'}%")
cols[1].metric("Unemployment Rate", f"{unemployment if unemployment is not None else 'N/A'}%")
cols[2].metric("Interest Rate", f"{interest_rate if interest_rate is not None else 'N/A'}%")
cols[3].metric("GDP Growth Rate", f"{gdp if gdp is not None else 'N/A'}%")
cols[4].metric("USD Index", f"{dollar_index if dollar_index is not None else 'N/A'}")

# ✅ Display sentiment
st.subheader("📉 Market Sentiment Based on Macro Score")
sentiment = score_market(inflation, unemployment, interest_rate, gdp, dollar_index)

color = {
    "Strong Bullish": "🟢",
    "Bullish": "🟩",
    "Neutral": "⚪",
    "Bearish": "🔻",
    "Strong Bearish": "🔴",
    "Insufficient Data": "❌"
}.get(sentiment, "❓")

st.markdown(f"### {color} **{sentiment}**")

st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

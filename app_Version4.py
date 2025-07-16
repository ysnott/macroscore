import streamlit as st
import requests
import datetime

API_KEY = "ed0f91db6215dd68eaa4aabaa84e3b9c"
BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

def get_inflation_rate(series_id="CPIAUCSL"):
    today = datetime.date.today()
    last_year = today - datetime.timedelta(days=365)

    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json",
        "observation_start": last_year.strftime("%Y-%m-%d"),
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json().get("observations", [])
        if len(data) >= 2:
            latest = float(data[-1]["value"])
            past = float(data[0]["value"])
            inflation_rate = ((latest - past) / past) * 100
            return round(inflation_rate, 2)
    return None

def get_fred_data(series_id, start_date="2023-01-01"):
    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json",
        "observation_start": start_date
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        observations = data.get("observations", [])
        if observations:
            try:
                return float(observations[-1]["value"])
            except:
                return None
    return None

INDICATORS = {
    "Unemployment Rate": "UNRATE",
    "Federal Funds Rate": "FEDFUNDS",
    "GDP Growth Rate": "A191RL1Q225SBEA",
    "US Dollar Index (DXY proxy)": "DTWEXAFEGS"
}

def score_market(inflation, unemployment, interest_rate, gdp, dollar_index):
    score = 0
    if inflation is not None and inflation < 3: score += 1
    if unemployment is not None and unemployment < 4.5: score += 1
    if interest_rate is not None and interest_rate < 3: score += 1
    if gdp is not None and gdp > 2: score += 1
    if dollar_index is not None and dollar_index > 110: score += 1

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

# Streamlit UI
st.set_page_config(page_title="MacroScore Dashboard", layout="wide")
st.title("📊 MacroScore Real-Time Dashboard")
st.markdown("This dashboard analyzes real-time macroeconomic data and gives a sentiment score for markets based on FRED indicators.")

with st.spinner("Fetching real-time data from FRED..."):
    inflation = get_inflation_rate()
    unemployment = get_fred_data(INDICATORS["Unemployment Rate"])
    interest_rate = get_fred_data(INDICATORS["Federal Funds Rate"])
    gdp = get_fred_data(INDICATORS["GDP Growth Rate"])
    dollar_index = get_fred_data(INDICATORS["US Dollar Index (DXY proxy)"])

st.subheader("📈 Latest Macroeconomic Indicators")
cols = st.columns(5)
cols[0].metric("Inflation Rate (CPI)", f"{inflation if inflation is not None else 'N/A'}%")
cols[1].metric("Unemployment Rate", f"{unemployment if unemployment is not None else 'N/A'}%")
cols[2].metric("Interest Rate", f"{interest_rate if interest_rate is not None else 'N/A'}%")
cols[3].metric("GDP Growth Rate", f"{gdp if gdp is not None else 'N/A'}%")
cols[4].metric("USD Index", f"{round(dollar_index, 2) if dollar_index is not None else 'N/A'}")

st.subheader("📉 Market Sentiment Based on Macro Score")
if None in [inflation, unemployment, interest_rate, gdp, dollar_index]:
    st.markdown("❌ Insufficient Data")
else:
    sentiment = score_market(inflation, unemployment, interest_rate, gdp, dollar_index)
    color = {
        "Strong Bullish": "🟢",
        "Bullish": "🟩",
        "Neutral": "⚪",
        "Bearish": "🔻",
        "Strong Bearish": "🔴"
    }.get(sentiment, "❓")
    st.markdown(f"### {color} **{sentiment}**")

st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

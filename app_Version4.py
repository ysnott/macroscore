import streamlit as st
import requests
import datetime
import pandas as pd

API_KEY = "abcdefghijklmnopqrstuvwxyz123456"
BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

def get_fred_data(series_id, start_date="2023-01-01"):
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
        if observations and observations[-1]["value"] != ".":
            return float(observations[-1]["value"])
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching data for {series_id}: {e}")
        return None

def get_fred_data_series(series_id, start_date="2023-01-01"):
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
        dates = []
        values = []
        for obs in observations:
            if obs["value"] != ".":
                dates.append(obs["date"])
                values.append(float(obs["value"]))
        return dates, values
    except:
        return [], []

INDICATORS = {
    "Inflation Rate (CPI)": "CPIAUCSL",
    "Unemployment Rate": "UNRATE",
    "Federal Funds Rate": "FEDFUNDS",
    "GDP Growth Rate": "A191RL1Q225SBEA",
    "US Dollar Index (DXY proxy)": "DTWEXAFEGS",
    "Debt-to-GDP Ratio": "GFDEGDQ188S",
    "Trade Balance": "BOPGSTB"
}

def score_market(inflation, unemployment, interest_rate, gdp, dollar_index):
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

st.set_page_config(page_title="MacroScore Dashboard", layout="wide")
st.title("📊 MacroScore Real-Time Dashboard")

st.markdown("This dashboard analyzes real-time macroeconomic data and gives a sentiment score for markets based on FRED indicators.")

with st.spinner("Fetching real-time data from FRED..."):
    inflation = get_fred_data(INDICATORS["Inflation Rate (CPI)"])
    unemployment = get_fred_data(INDICATORS["Unemployment Rate"])
    interest_rate = get_fred_data(INDICATORS["Federal Funds Rate"])
    gdp = get_fred_data(INDICATORS["GDP Growth Rate"])
    dollar_index = get_fred_data(INDICATORS["US Dollar Index (DXY proxy)"])
    debt_to_gdp = get_fred_data(INDICATORS["Debt-to-GDP Ratio"])
    trade_balance = get_fred_data(INDICATORS["Trade Balance"])

st.subheader("📈 Latest Macroeconomic Indicators")
cols = st.columns(7)
cols[0].metric("Inflation Rate (CPI)", f"{inflation}%")
cols[1].metric("Unemployment Rate", f"{unemployment}%")
cols[2].metric("Interest Rate", f"{interest_rate}%")
cols[3].metric("GDP Growth Rate", f"{gdp}%")
cols[4].metric("USD Index", f"{dollar_index}")
cols[5].metric("Debt-to-GDP", f"{debt_to_gdp}%")
cols[6].metric("Trade Balance", f"${trade_balance}B")

st.subheader("📉 Market Sentiment Based on Macro Score")
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

# Trend visualization for the last 6 months
st.subheader("📊 Indicators Trend - Last 6 Months")
timeframe = st.selectbox("Select timeframe for analysis:", ["Last 6 Months", "Last 1 Year", "Last 5 Years"])
days_map = {"Last 6 Months": 180, "Last 1 Year": 365, "Last 5 Years": 1825}
selected_days = days_map[timeframe]

for name, series_id in INDICATORS.items():
    dates, values = get_fred_data_series(series_id, (datetime.datetime.now() - datetime.timedelta(days=selected_days)).strftime("%Y-%m-%d"))
    if dates:
        df = pd.DataFrame({"Date": dates, "Value": values})
        df["Rolling Avg"] = df["Value"].rolling(window=7).mean()
        st.line_chart(df.set_index("Date"), use_container_width=True)
    else:
        st.write(f"No data available for {name}")

# User input for hypothetical scenarios
st.subheader("📋 Hypothetical Scenarios")
inflation_input = st.slider("Hypothetical Inflation Rate (CPI)", 0.0, 10.0, inflation or 2.0)
unemployment_input = st.slider("Hypothetical Unemployment Rate", 0.0, 10.0, unemployment or 4.0)
interest_rate_input = st.slider("Hypothetical Interest Rate", 0.0, 10.0, interest_rate or 2.5)

new_sentiment = score_market(inflation_input, unemployment_input, interest_rate_input, gdp, dollar_index)
st.markdown(f"### Hypothetical Market Sentiment: {color.get(new_sentiment, '❓')} **{new_sentiment}**")
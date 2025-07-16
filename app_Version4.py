import os
import streamlit as st
import requests
import datetime

# --- API KEYS & URLS ---
FRED_API_KEY = os.getenv("FRED_API_KEY", "e072fbb3098e26e777214caac7c036d3")
FOREX_API_KEY = "40c602106bf2e6545af3686d76a164b8"
FOREX_API_URL = f"https://v6.exchangerate-api.com/v6/{FOREX_API_KEY}/latest/USD"
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# --- Indicators & Forex Pairs ---
INDICATORS = {
    "CPI Index": "CPIAUCSL",
    "Unemployment Rate": "UNRATE",
    "Federal Funds Rate": "FEDFUNDS",
    "GDP Growth Rate": "A191RL1Q225SBEA",
    "USD Index (DXY Approx)": "DTWEXBGS"
}

FOREX_PAIRS = [
    "EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", "USD/CAD", "USD/CHF", "NZD/USD",
    "EUR/GBP", "EUR/AUD", "EUR/CAD", "EUR/CHF", "GBP/JPY", "AUD/JPY", "CAD/JPY",
    "CHF/JPY", "NZD/JPY", "GBP/CAD", "GBP/CHF", "AUD/CAD", "AUD/CHF", "CAD/CHF",
    "NZD/CAD", "NZD/CHF"
]

# --- Helpers ---
def format_metric(value, suffix=""):
    try:
        return f"{float(value):.2f}{suffix}" if value is not None else "N/A"
    except:
        return "N/A"

@st.cache_data(ttl=3600)
def get_fred_data(series_id):
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc"
    }
    try:
        response = requests.get(FRED_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        observations = [
            obs for obs in data["observations"] if obs["value"] not in (".", "")
        ]
        if not observations or len(observations) < 2:
            return None

        latest = float(observations[0]["value"])
        previous = float(observations[12]["value"])  # 12 months ago
        if series_id == "CPIAUCSL":
            yoy_inflation = ((latest - previous) / previous) * 100
            return round(yoy_inflation, 2)
        return latest
    except Exception:
        return None

@st.cache_data(ttl=600)
def fetch_forex_rates(pairs):
    try:
        response = requests.get(FOREX_API_URL)
        response.raise_for_status()
        data = response.json()
        rates = data.get("conversion_rates", {})
        result = {}
        for pair in pairs:
            base, quote = pair.split('/')
            try:
                if base == "USD":
                    rate = rates.get(quote)
                elif quote == "USD":
                    base_rate = rates.get(base)
                    rate = 1 / base_rate if base_rate else None
                else:
                    base_rate = rates.get(base)
                    quote_rate = rates.get(quote)
                    rate = (1 / base_rate) * quote_rate if base_rate and quote_rate else None
                result[pair] = round(rate, 5) if rate else "N/A"
            except:
                result[pair] = "N/A"
        return result
    except Exception:
        return {pair: "N/A" for pair in pairs}

def score_market(inflation, unemployment, interest_rate, gdp, dollar_index):
    score = 0
    if inflation is not None and inflation < 3: score += 1
    if unemployment is not None and unemployment < 4.5: score += 1
    if interest_rate is not None and interest_rate < 3: score += 1
    if gdp is not None and gdp > 0: score += 1
    if dollar_index is not None and dollar_index > 95: score += 1

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

# --- Streamlit UI ---
st.set_page_config(page_title="MacroScore Dashboard", layout="wide")
st.title("📊 MacroScore Real-Time Dashboard with Forex Pairs")
st.markdown("Real-time macroeconomic indicators from FRED + live Forex rates from ExchangeRate-API")

# --- Macroeconomic Data ---
with st.spinner("Fetching macroeconomic data..."):
    inflation = get_fred_data(INDICATORS["CPI Index"])
    unemployment = get_fred_data(INDICATORS["Unemployment Rate"])
    interest_rate = get_fred_data(INDICATORS["Federal Funds Rate"])
    gdp = get_fred_data(INDICATORS["GDP Growth Rate"])
    dollar_index = get_fred_data(INDICATORS["USD Index (DXY Approx)"])

st.subheader("📈 Latest Macroeconomic Indicators")
cols = st.columns(5)
cols[0].metric("Inflation Rate (YoY %)", format_metric(inflation, "%"))
cols[1].metric("Unemployment Rate", format_metric(unemployment, "%"))
cols[2].metric("Interest Rate", format_metric(interest_rate, "%"))
cols[3].metric("GDP Growth Rate", format_metric(gdp, "%"))
cols[4].metric("USD Index (Approx)", format_metric(dollar_index))

# --- Sentiment Analysis ---
sentiment = score_market(inflation, unemployment, interest_rate, gdp, dollar_index)
sentiment_color = {
    "Strong Bullish": "🟢",
    "Bullish": "🟩",
    "Neutral": "⚪",
    "Bearish": "🔻",
    "Strong Bearish": "🔴"
}.get(sentiment, "❓")

st.subheader("📉 Market Sentiment Based on Macro Score")
st.markdown(f"### {sentiment_color} **{sentiment}**")

# --- Forex Section ---
with st.spinner("Fetching live Forex rates..."):
    forex_rates = fetch_forex_rates(FOREX_PAIRS)

st.subheader("💱 Forex Pairs Rates")
cols = st.columns(3)
for i, pair in enumerate(FOREX_PAIRS):
    rate = forex_rates.get(pair)
    cols[i % 3].markdown(f"**{pair}**: {rate}")

# --- Footer ---
st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.markdown("---")
st.markdown("👨‍💻 Created by **YSNOTT**")

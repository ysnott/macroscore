import os
import streamlit as st
import requests
import datetime

# --- API KEYS & URLS ---
FRED_API_KEY = os.getenv("FRED_API_KEY", "e072fbb3098e26e777214caac7c036d3")
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
FOREX_API_URL = "https://api.exchangerate.host/latest"

# --- Macro Indicators & Pairs ---
INDICATORS = {
    "Inflation Rate (CPI YoY %)": "CPIAUCSL",
    "Unemployment Rate": "UNRATE",
    "Federal Funds Rate": "FEDFUNDS",
    "GDP Growth Rate": "A191RL1Q225SBEA",
    "USD Index": "DTWEXBGS"
}

FOREX_PAIRS = [
    "EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", "USD/CAD", "USD/CHF", "NZD/USD",
    "EUR/GBP", "EUR/AUD", "EUR/CAD", "EUR/CHF", "GBP/JPY", "AUD/JPY", "CAD/JPY",
    "CHF/JPY", "NZD/JPY", "GBP/CAD", "GBP/CHF", "AUD/CAD", "AUD/CHF", "CAD/CHF",
    "NZD/CAD", "NZD/CHF"
]

# --- Helper: Metric Format ---
def format_metric(value, suffix=""):
    try:
        return f"{float(value):.2f}{suffix}" if value is not None else "N/A"
    except:
        return "N/A"

# --- Functions ---
@st.cache_data(ttl=3600)
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
        observations = data.get("observations", [])
        valid_obs = [obs for obs in observations if obs.get("value") not in (".", "")]
        return float(valid_obs[-1]["value"]) if valid_obs else None
    except Exception as e:
        st.warning(f"Unable to fetch data for {series_id}.")
        return None

@st.cache_data(ttl=600)
def fetch_forex_rates(pairs):
    base = "USD"
    try:
        url = f"{FOREX_API_URL}?base={base}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        rates = {}
        for pair in pairs:
            base_curr, quote_curr = pair.split('/')
            try:
                if base_curr == base:
                    rate = data['rates'].get(quote_curr)
                elif quote_curr == base:
                    base_curr_rate = data['rates'].get(base_curr)
                    rate = 1 / base_curr_rate if base_curr_rate else None
                else:
                    base_curr_rate = data['rates'].get(base_curr)
                    quote_curr_rate = data['rates'].get(quote_curr)
                    rate = (1 / base_curr_rate) * quote_curr_rate if base_curr_rate and quote_curr_rate else None
                rates[pair] = round(rate, 5) if rate else "N/A"
            except:
                rates[pair] = "N/A"
        return rates
    except Exception as e:
        st.warning("Unable to fetch Forex data.")
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

# --- Streamlit App ---
st.set_page_config(page_title="MacroScore Dashboard with Forex", layout="wide")
st.title("📊 MacroScore Real-Time Dashboard with Forex Pairs")
st.markdown("Dashboard يحلل المؤشرات الاقتصادية من FRED ويربطها بأسعار الفوركس (Forex) الحية من exchangerate.host")

# --- Data Section ---
with st.spinner("Fetching macroeconomic data..."):
    inflation = get_fred_data(INDICATORS["Inflation Rate (CPI YoY %)"])
    unemployment = get_fred_data(INDICATORS["Unemployment Rate"])
    interest_rate = get_fred_data(INDICATORS["Federal Funds Rate"])
    gdp = get_fred_data(INDICATORS["GDP Growth Rate"])
    dollar_index = get_fred_data(INDICATORS["USD Index"])

# --- Metrics Display ---
st.subheader("📈 Latest Macroeconomic Indicators")
cols = st.columns(5)
cols[0].metric("Inflation Rate (CPI YoY %)", format_metric(inflation, "%"))
cols[1].metric("Unemployment Rate", format_metric(unemployment, "%"))
cols[2].metric("Interest Rate", format_metric(interest_rate, "%"))
cols[3].metric("GDP Growth Rate", format_metric(gdp, "%"))
cols[4].metric("USD Index", format_metric(dollar_index))

# --- Sentiment Score ---
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

# --- Forex Rates Section ---
with st.spinner("Fetching live Forex rates..."):
    forex_rates = fetch_forex_rates(FOREX_PAIRS)

st.subheader("💱 Forex Pairs Rates & Sentiment")
cols = st.columns(3)
for i, pair in enumerate(FOREX_PAIRS):
    rate = forex_rates.get(pair)
    cols[i % 3].markdown(f"**{pair}**: {rate}")

st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

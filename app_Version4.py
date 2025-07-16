import streamlit as st
import requests
import datetime

# --- API KEYS & URLS ---
FRED_API_KEY = "ed0f91db6215dd68eaa4aabaa84e3b9c"  # API key FRED حقيقية
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

FOREX_API_URL = "https://api.exchangerate.host/latest"
FOREX_API_KEY = "40c602106bf2e6545af3686d76a164b8"  # API key exchangerate.host

# --- Macro Indicators & Pairs ---
INDICATORS = {
    "Inflation Rate (CPI YoY %)": "CPIAUCSL",
    "Unemployment Rate": "UNRATE",
    "Federal Funds Rate": "FEDFUNDS",
    "GDP Growth Rate": "A191RL1Q225SBEA",
    "USD Index": "DTWEXAFEGS"
}

FOREX_PAIRS = [
    "EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", "USD/CAD", "USD/CHF", "NZD/USD",
    "EUR/GBP", "EUR/AUD", "EUR/CAD", "EUR/CHF", "GBP/JPY", "AUD/JPY", "CAD/JPY",
    "CHF/JPY", "NZD/JPY", "GBP/CAD", "GBP/CHF", "AUD/CAD", "AUD/CHF", "CAD/CHF",
    "NZD/CAD", "NZD/CHF"
]

# --- Functions ---

def get_fred_data(series_id, start_date="2022-01-01"):
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date
    }
    try:
        response = requests.get(FRED_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        observations = data.get("observations", [])
        # Find the last valid numeric value (skip '.' or missing)
        for obs in reversed(observations):
            value = obs.get("value")
            if value not in (".", ""):
                return float(value)
        return None
    except Exception as e:
        st.error(f"Error fetching data for {series_id}: {e}")
        return None

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

def fetch_forex_rates(pairs):
    base = "USD"
    try:
        # API call - Add apikey in URL if needed, or remove if not required
        url = f"{FOREX_API_URL}?base={base}&apikey={FOREX_API_KEY}"
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
                    rate = 1 / base_curr_rate if base_curr_rate and base_curr_rate != 0 else None
                else:
                    base_curr_rate = data['rates'].get(base_curr)
                    quote_curr_rate = data['rates'].get(quote_curr)
                    if base_curr_rate and quote_curr_rate:
                        rate = (1 / base_curr_rate) * quote_curr_rate
                    else:
                        rate = None
                rates[pair] = round(rate, 5) if rate else None
            except:
                rates[pair] = None
        return rates
    except Exception as e:
        st.error(f"Error fetching Forex data: {e}")
        return {pair: None for pair in pairs}

# --- Streamlit UI ---
st.set_page_config(page_title="MacroScore Dashboard with Forex", layout="wide")
st.title("📊 MacroScore Real-Time Dashboard with Forex Pairs")
st.markdown("Dashboard يحلل المؤشرات الاقتصادية من FRED ويربطها بأسعار الفوركس (Forex) الحية من exchangerate.host")

with st.spinner("Fetching macroeconomic data..."):
    inflation = get_fred_data(INDICATORS["Inflation Rate (CPI YoY %)"])
    unemployment = get_fred_data(INDICATORS["Unemployment Rate"])
    interest_rate = get_fred_data(INDICATORS["Federal Funds Rate"])
    gdp = get_fred_data(INDICATORS["GDP Growth Rate"])
    dollar_index = get_fred_data(INDICATORS["USD Index"])

st.subheader("📈 Latest Macroeconomic Indicators")
cols = st.columns(5)
cols[0].metric("Inflation Rate (CPI YoY %)", f"{inflation:.2f}%" if inflation is not None else "N/A")
cols[1].metric("Unemployment Rate", f"{unemployment:.2f}%" if unemployment is not None else "N/A")
cols[2].metric("Interest Rate", f"{interest_rate:.2f}%" if interest_rate is not None else "N/A")
cols[3].metric("GDP Growth Rate", f"{gdp:.2f}%" if gdp is not None else "N/A")
cols[4].metric("USD Index", f"{dollar_index:.2f}" if dollar_index is not None else "N/A")

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

with st.spinner("Fetching live Forex rates..."):
    forex_rates = fetch_forex_rates(FOREX_PAIRS)

st.subheader("💱 Forex Pairs Rates & Sentiment")
for pair in FOREX_PAIRS:
    rate = forex_rates.get(pair)
    rate_display = f"{rate:.5f}" if rate else "N/A"
    st.write(f"**{pair}**: {rate_display}")

st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

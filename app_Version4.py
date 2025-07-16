import streamlit as st
import requests
import datetime

API_KEY = "ed0f91db6215dd68eaa4aabaa84e3b9c"
BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

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
            return observations
    return None

def get_cpi_inflation(series_id="CPIAUCSL"):
    observations = get_fred_data(series_id)
    if observations and len(observations) >= 13:  # على الأقل سنة + شهر
        latest_cpi = float(observations[-1]["value"])
        cpi_1year_ago = float(observations[-13]["value"])
        inflation_rate = ((latest_cpi - cpi_1year_ago) / cpi_1year_ago) * 100
        return round(inflation_rate, 2)
    return None

def get_latest_value(series_id):
    observations = get_fred_data(series_id)
    if observations:
        try:
            return round(float(observations[-1]["value"]), 2)
        except:
            return None
    return None

INDICATORS = {
    "Inflation Rate (CPI)": "CPIAUCSL",
    "Unemployment Rate": "UNRATE",
    "Federal Funds Rate": "FEDFUNDS",
    "GDP Growth Rate": "A191RL1Q225SBEA",
    "US Dollar Index (DXY proxy)": "DTWEXAFEGS"
}

FOREX_PAIRS = [
    "EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", "USD/CAD", "USD/CHF", "NZD/USD",
    "EUR/GBP", "EUR/AUD", "EUR/CAD", "EUR/CHF", "GBP/JPY", "AUD/JPY", "CAD/JPY", "CHF/JPY", "NZD/JPY",
    "GBP/CAD", "GBP/CHF", "AUD/CAD", "AUD/CHF", "CAD/CHF", "NZD/CAD", "NZD/CHF"
]

FOREX_API_URL = "https://api.exchangerate.host/latest"

def fetch_forex_rates(pairs):
    base = "USD"
    response = requests.get(f"{FOREX_API_URL}?base={base}")
    rates = {}
    if response.status_code == 200:
        data = response.json()
        for pair in pairs:
            base_curr, quote_curr = pair.split('/')
            # نجيب السعر مباشرة بناءً على USD كـ base أو نقلب لو العكس
            if base_curr == base:
                rate = data['rates'].get(quote_curr)
            elif quote_curr == base:
                rate = 1 / data['rates'].get(base_curr, 0) if data['rates'].get(base_curr, 0) != 0 else None
            else:
                # حساب السعر للزوج الغير USD كـ base
                rate_base_to_usd = 1 / data['rates'].get(base_curr, 0) if data['rates'].get(base_curr, 0) != 0 else None
                rate = rate_base_to_usd * data['rates'].get(quote_curr, 0) if rate_base_to_usd and data['rates'].get(quote_curr, 0) else None
            
            if rate:
                rates[pair] = round(rate, 5)
            else:
                rates[pair] = None
    return rates

def score_market(inflation, unemployment, interest_rate, gdp, dollar_index):
    if None in [inflation, unemployment, interest_rate, gdp, dollar_index]:
        return "❌ Insufficient Data"
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

def forex_sentiment(rate, inflation):
    # مثال بسيط: إذا السعر ارتفع و التضخم أقل من 3% => إيجابي (Bullish)
    if rate is None or inflation is None:
        return "N/A"
    if rate > 1 and inflation < 3:
        return "Bullish"
    elif rate < 1 and inflation > 3:
        return "Bearish"
    else:
        return "Neutral"

st.set_page_config(page_title="MacroScore Dashboard with Forex", layout="wide")
st.title("📊 MacroScore Real-Time Dashboard with Forex Pairs")
st.markdown("Dashboard يحلل المؤشرات الاقتصادية من FRED ويربطها بأسعار الفوركس (Forex) الحية من exchangerate.host")

with st.spinner("Fetching macroeconomic data..."):
    inflation = get_cpi_inflation()
    unemployment = get_latest_value(INDICATORS["Unemployment Rate"])
    interest_rate = get_latest_value(INDICATORS["Federal Funds Rate"])
    gdp = get_latest_value(INDICATORS["GDP Growth Rate"])
    dollar_index = get_latest_value(INDICATORS["US Dollar Index (DXY proxy)"])

st.subheader("📈 Latest Macroeconomic Indicators")
cols = st.columns(5)
cols[0].metric("Inflation Rate (CPI YoY %)", f"{inflation if inflation is not None else 'N/A'}%")
cols[1].metric("Unemployment Rate", f"{unemployment if unemployment is not None else 'N/A'}%")
cols[2].metric("Interest Rate", f"{interest_rate if interest_rate is not None else 'N/A'}%")
cols[3].metric("GDP Growth Rate", f"{gdp if gdp is not None else 'N/A'}%")
cols[4].metric("USD Index", f"{dollar_index if dollar_index is not None else 'N/A'}")

st.subheader("📉 Market Sentiment Based on Macro Score")
sentiment = score_market(inflation, unemployment, interest_rate, gdp, dollar_index)
color = {
    "Strong Bullish": "🟢",
    "Bullish": "🟩",
    "Neutral": "⚪",
    "Bearish": "🔻",
    "Strong Bearish": "🔴",
    "❌ Insufficient Data": "❌"
}.get(sentiment, "❓")
st.markdown(f"### {color} **{sentiment}**")

with st.spinner("Fetching Forex rates..."):
    forex_rates = fetch_forex_rates(FOREX_PAIRS)

st.subheader("💱 Forex Pairs Rates & Sentiment")
for pair in FOREX_PAIRS:
    rate = forex_rates.get(pair)
    pair_sentiment = forex_sentiment(rate, inflation)
    st.write(f"**{pair}**: {rate if rate else 'N/A'} — {pair_sentiment}")

st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

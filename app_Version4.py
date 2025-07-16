import streamlit as st
import requests
import datetime

# === FRED API CONFIG ===
API_KEY = "ed0f91db6215dd68eaa4aabaa84e3b9c"
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# === Forex Pairs List ===
PAIRS = [
    ("EUR", "USD"), ("USD", "JPY"), ("GBP", "USD"), ("AUD", "USD"),
    ("USD", "CAD"), ("USD", "CHF"), ("NZD", "USD"),
    ("EUR", "GBP"), ("EUR", "AUD"), ("EUR", "CAD"), ("EUR", "CHF"),
    ("GBP", "JPY"), ("AUD", "JPY"), ("CAD", "JPY"), ("CHF", "JPY"), ("NZD", "JPY"),
    ("GBP", "CAD"), ("GBP", "CHF"), ("AUD", "CAD"), ("AUD", "CHF"),
    ("CAD", "CHF"), ("NZD", "CAD"), ("NZD", "CHF")
]

# === Get FRED Data Function ===
def get_fred_data(series_id, start_date="2023-01-01"):
    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json",
        "observation_start": start_date
    }
    try:
        response = requests.get(FRED_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        observations = data.get("observations", [])
        # ترجع آخر قيمة صالحة
        for obs in reversed(observations):
            try:
                val = float(obs["value"])
                if val != -9999999999:  # قيمة فاضية في بعض الحالات
                    return val
            except:
                continue
        return None
    except Exception as e:
        st.error(f"Error fetching data for {series_id}: {e}")
        return None

# === Get Forex Rate Function ===
def get_exchange_rate(base, target):
    url = f"https://api.exchangerate.host/latest?base={base}&symbols={target}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data['rates'].get(target, None)
    except Exception:
        return None

# === Macroeconomic Indicators & Their FRED IDs ===
INDICATORS = {
    "Inflation Rate (CPI)": "CPIAUCSL",
    "Unemployment Rate": "UNRATE",
    "Federal Funds Rate": "FEDFUNDS",
    "GDP Growth Rate": "A191RL1Q225SBEA",
    "US Dollar Index (DXY proxy)": "DTWEXAFEGS"
}

# === Score Market Based on Macroeconomics ===
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

# === Streamlit UI ===
st.set_page_config(page_title="📊 MacroScore + Forex Dashboard", layout="wide")
st.title("📊 MacroScore Real-Time Dashboard with Forex Pairs")

st.markdown("Dashboard يحلل المؤشرات الاقتصادية من FRED ويربطها بأسعار الفوركس (Forex)")

# Fetch all macro data
with st.spinner("Fetching macroeconomic data from FRED..."):
    inflation = get_fred_data(INDICATORS["Inflation Rate (CPI)"])
    unemployment = get_fred_data(INDICATORS["Unemployment Rate"])
    interest_rate = get_fred_data(INDICATORS["Federal Funds Rate"])
    gdp = get_fred_data(INDICATORS["GDP Growth Rate"])
    dollar_index = get_fred_data(INDICATORS["US Dollar Index (DXY proxy)"])

# Display macro indicators
st.subheader("📈 Latest Macroeconomic Indicators")
cols_macro = st.columns(5)
cols_macro[0].metric("Inflation Rate (CPI)", f"{inflation if inflation is not None else 'N/A'}%")
cols_macro[1].metric("Unemployment Rate", f"{unemployment if unemployment is not None else 'N/A'}%")
cols_macro[2].metric("Interest Rate", f"{interest_rate if interest_rate is not None else 'N/A'}%")
cols_macro[3].metric("GDP Growth Rate", f"{gdp if gdp is not None else 'N/A'}%")
cols_macro[4].metric("USD Index", f"{dollar_index if dollar_index is not None else 'N/A'}")

# Market Sentiment
sentiment = score_market(inflation, unemployment, interest_rate, gdp, dollar_index)

color = {
    "Strong Bullish": "🟢",
    "Bullish": "🟩",
    "Neutral": "⚪",
    "Bearish": "🔻",
    "Strong Bearish": "🔴"
}.get(sentiment, "❓")

st.subheader(f"📉 Market Sentiment Based on Macro Score: {color} **{sentiment}**")

# Forex Pairs Rates & Sentiment
st.subheader("💱 Forex Pairs Rates & Sentiment")

cols = st.columns(4)
for i, (base, target) in enumerate(PAIRS):
    rate = get_exchange_rate(base, target)
    if rate is None:
        rate_str = "N/A"
        status = "N/A"
    else:
        rate_str = f"{rate:.4f}"
        # الربط بسيط: إذا السوق صاعد (Bullish) نعرض صعود للأزواج اللي فيها USD كعملة أساسية أو مقابلة
        if sentiment in ["Strong Bullish", "Bullish"]:
            if base == "USD" or target == "USD":
                status = "📈 Strong"
            else:
                status = "➖ Neutral"
        elif sentiment == "Neutral":
            status = "➖ Neutral"
        else:
            if base == "USD" or target == "USD":
                status = "📉 Weak"
            else:
                status = "➖ Neutral"

    cols[i % 4].metric(f"{base}/{target}", rate_str, status)

st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

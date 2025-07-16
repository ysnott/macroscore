import streamlit as st
import requests
import datetime

API_KEY = "ed0f91db6215dd68eaa4aabaa84e3b9c"
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# دالة جلب بيانات FRED مع معالجة الخطأ
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
        # نرجع آخر قيمة صالحة
        for obs in reversed(observations):
            try:
                val = float(obs["value"])
                if val != -999999:  # قيمة فارغة في FRED
                    return val
            except:
                continue
        return None
    except Exception as e:
        st.error(f"Error fetching data for {series_id}: {e}")
        return None

# دالة جلب سعر الفوركس لكل زوج
def get_forex_rate(pair):
    base, quote = pair.split('/')
    url = f"https://api.exchangerate.host/latest?base={base}&symbols={quote}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        rate = data.get("rates", {}).get(quote)
        return rate
    except Exception as e:
        st.warning(f"Error fetching rate for {pair}: {e}")
        return None

# مؤشرات FRED
INDICATORS = {
    "Inflation Rate (CPI)": "CPIAUCSL",
    "Unemployment Rate": "UNRATE",
    "Federal Funds Rate": "FEDFUNDS",
    "GDP Growth Rate": "A191RL1Q225SBEA",
    "US Dollar Index (DXY proxy)": "DTWEXAFEGS"
}

# أزواج الفوركس الرئيسية والثانوية والكروس
FOREX_PAIRS = [
    "EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", "USD/CAD", "USD/CHF", "NZD/USD",
    "EUR/GBP", "EUR/AUD", "EUR/CAD", "EUR/CHF", "GBP/JPY", "AUD/JPY", "CAD/JPY", "CHF/JPY", "NZD/JPY",
    "GBP/CAD", "GBP/CHF", "AUD/CAD", "AUD/CHF", "CAD/CHF", "NZD/CAD", "NZD/CHF"
]

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

st.set_page_config(page_title="MacroScore Real-Time Dashboard", layout="wide")
st.title("📊 MacroScore Real-Time Dashboard with Forex Pairs")

st.markdown("This dashboard analyzes real-time macroeconomic data from FRED and links it with live Forex pairs rates from exchangerate.host.")

with st.spinner("Fetching real-time macroeconomic data from FRED..."):
    inflation = get_fred_data(INDICATORS["Inflation Rate (CPI)"])
    unemployment = get_fred_data(INDICATORS["Unemployment Rate"])
    interest_rate = get_fred_data(INDICATORS["Federal Funds Rate"])
    gdp = get_fred_data(INDICATORS["GDP Growth Rate"])
    dollar_index = get_fred_data(INDICATORS["US Dollar Index (DXY proxy)"])

st.subheader("📈 Latest Macroeconomic Indicators")
cols = st.columns(5)
cols[0].metric("Inflation Rate (CPI)", f"{inflation:.2f}%" if inflation is not None else "N/A")
cols[1].metric("Unemployment Rate", f"{unemployment:.2f}%" if unemployment is not None else "N/A")
cols[2].metric("Interest Rate", f"{interest_rate:.2f}%" if interest_rate is not None else "N/A")
cols[3].metric("GDP Growth Rate", f"{gdp:.2f}%" if gdp is not None else "N/A")
cols[4].metric("USD Index", f"{dollar_index:.2f}" if dollar_index is not None else "N/A")

sentiment = score_market(inflation, unemployment, interest_rate, gdp, dollar_index)
color_map = {
    "Strong Bullish": "🟢",
    "Bullish": "🟩",
    "Neutral": "⚪",
    "Bearish": "🔻",
    "Strong Bearish": "🔴"
}
color = color_map.get(sentiment, "❓")

st.subheader("📉 Market Sentiment Based on Macro Score")
st.markdown(f"### {color} **{sentiment}**")

st.subheader("💱 Forex Pairs Rates & Sentiment")

# جدول أسعار الفوركس مع الحالة (simple sentiment based on مقارنة السعر مع 1.0 كمثال)
for pair in FOREX_PAIRS:
    rate = get_forex_rate(pair)
    if rate is None:
        display_rate = "N/A"
        sentiment_pair = "N/A"
    else:
        display_rate = f"{rate:.4f}"
        # مثال بسيط: إذا السعر فوق 1.0 -> Bullish, تحت -> Bearish (يمكن تطوير التحليل لاحقًا)
        sentiment_pair = "Bullish" if rate > 1.0 else "Bearish" if rate < 1.0 else "Neutral"

    st.write(f"**{pair}** — Rate: {display_rate} — Sentiment: {sentiment_pair}")

st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

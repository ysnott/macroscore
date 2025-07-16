import streamlit as st
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

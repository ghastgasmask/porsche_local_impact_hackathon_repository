import streamlit as st
import requests
import os
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Калькулятор валют", page_icon=None, layout="wide")

# Custom CSS for modern styling
st.markdown("""
<style>
    .calc-header {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1.5rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1.5rem;
    }
    .result-box {
        background-color: #e8f4fd;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #b3d7ff;
        text-align: center;
        margin-top: 1rem;
    }
    .result-text {
        font-size: 2rem;
        font-weight: bold;
        color: #0056b3;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="calc-header">Конвертер и калькулятор валют</p>', unsafe_allow_html=True)

# Get API Key from environment
api_key = os.getenv("EXCHANGERATE_API_KEY", "")

# Default fallback rates (in case API key is missing or endpoint is down)
MOCK_RATES = {
    "USDUSD": 1.0,
    "USDEUR": 0.92,
    "USDGBP": 0.79,
    "USDCHF": 0.91,
    "USDCAD": 1.37,
    "USDJPY": 155.50,
    "USDAUD": 1.51,
    "USDCNY": 7.24,
    "USDSGD": 1.35,
}

@st.cache_data(ttl=3600)  # Cache rates for 1 hour
def fetch_exchange_rates(key):
    if not key:
        return None, "API-ключ отсутствует. Используются локальные резервные курсы."
    
    try:
        # exchangerate.host API endpoint
        url = f"http://api.exchangerate.host/live?access_key={key}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("success"):
            return data.get("quotes"), None
        else:
            error_info = data.get("error", {}).get("info", "Неизвестная ошибка API")
            return None, f"Ошибка API: {error_info}. Используются локальные резервные курсы."
    except Exception as e:
        return None, f"Ошибка соединения: {str(e)}. Используются локальные резервные курсы."

# Fetch rates
quotes, err = fetch_exchange_rates(api_key)

if err:
    st.warning(err)
    quotes = MOCK_RATES

# Extract available currencies
currencies = sorted(list(set([k[3:] for k in quotes.keys() if k.startswith("USD")])))

if "USD" not in currencies:
    currencies.append("USD")
currencies = sorted(list(set(currencies)))

# UI Layout
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### Детали конвертации")
    amount = st.number_input("Сумма для конвертации", min_value=0.0, value=1000.0, step=100.0)
    
    from_currency = st.selectbox("Исходная валюта", currencies, index=currencies.index("USD") if "USD" in currencies else 0)
    to_currency = st.selectbox("Целевая валюта", currencies, index=currencies.index("EUR") if "EUR" in currencies else 0)

with col2:
    st.markdown("### Текущий результат")
    
    # Calculate conversion
    key_from = f"USD{from_currency}"
    key_to = f"USD{to_currency}"
    
    rate_from = quotes.get(key_from, 1.0) if from_currency != "USD" else 1.0
    rate_to = quotes.get(key_to, 1.0) if to_currency != "USD" else 1.0
    
    # Perform conversion: convert to USD base first, then convert to target
    usd_amount = amount / rate_from
    converted_amount = usd_amount * rate_to
    
    implied_rate = rate_to / rate_from
    
    st.markdown(f"""
    <div class="result-box">
        <p style="margin: 0; font-size: 1.1rem; color: #555;">{amount:,.2f} {from_currency} =</p>
        <p class="result-text">{converted_amount:,.2f} {to_currency}</p>
        <p style="margin: 0; font-size: 0.9rem; color: #666;">Кросс курс: 1 {from_currency} = {implied_rate:.6f} {to_currency}</p>
    </div>
    """, unsafe_allow_html=True)

# Visualizing top currency comparisons
st.markdown("---")
st.markdown("### Сравнение обменных курсов (Базовый USD)")

# Create data for plotting
plot_data = []
for k, v in quotes.items():
    curr = k[3:]
    if curr in ["EUR", "GBP", "CHF", "CAD", "JPY", "AUD", "SGD", "CNY"]:
        plot_data.append({"Валюта": curr, "Курс к USD": v})

if plot_data:
    df_plot = pd.DataFrame(plot_data)
    fig = px.bar(df_plot, x="Валюта", y="Курс к USD", title="Единиц валюты за 1 USD",
                 labels={"Курс к USD": "Обменный курс"}, color="Валюта",
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

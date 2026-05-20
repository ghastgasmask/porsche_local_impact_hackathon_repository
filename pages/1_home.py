"""
Главная панель системы
"""

import streamlit as st
import pandas as pd
from modules.session_data import ensure_session_data

st.set_page_config(page_title="Главная панель", page_icon=None, layout="wide")
ensure_session_data()

# Кастомный CSS для фиолетового дизайна
st.markdown("""
<style>
    /* Заголовки */
    h1, h2, h3 {
        color: #3c096c !important;
        font-family: 'Outfit', 'Inter', sans-serif !important;
        font-weight: 800 !important;
    }
    
    /* Разделитель */
    hr {
        border-color: #ebdfff !important;
    }
    
    /* Стилизация Streamlit метрик */
    [data-testid="stMetricValue"] {
        color: #5a189a !important;
        font-weight: 800 !important;
        font-size: 1.8rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: #7b2cbf !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05rem !important;
    }
    [data-testid="stMetric"] {
        background-color: #fcfaff !important;
        border: 1px solid #ebdfff !important;
        border-left: 5px solid #7b2cbf !important;
        border-radius: 10px !important;
        padding: 0.8rem 1rem !important;
        box-shadow: 0 4px 12px rgba(123, 44, 191, 0.03) !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("### Главная панель управления")

# Получаем данные из session_state
accounts_df = st.session_state.accounts_df
transactions_df = st.session_state.transactions_df
scheduled_payments_df = st.session_state.scheduled_payments_df
expected_inflows_df = st.session_state.expected_inflows_df

# Импортируем модули
from modules.cash_allocator import SmartCashAllocator
from modules.reserve_optimizer import ReserveOptimizer

# Инициализируем модули
allocator = SmartCashAllocator(accounts_df, transactions_df, scheduled_payments_df)
optimizer = ReserveOptimizer(accounts_df, transactions_df, scheduled_payments_df, expected_inflows_df)

st.markdown("### Ключевые показатели")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_balance = accounts_df['current_balance'].sum()
    st.metric("Общий баланс", f"${total_balance:,.0f}")

with col2:
    num_accounts = len(accounts_df)
    st.metric("Всего счетов", num_accounts)

with col4:
    efficiency = optimizer.calculate_reserve_efficiency_score()
    st.metric("Эффективность", f"{efficiency['score']:.0f}/100")

st.divider()

# Статус счетов
st.markdown("### Здоровье счетов")

health_df = allocator.get_account_health_status()

col1, col2, col3 = st.columns(3)

with col1:
    num_optimal = len(health_df[health_df['status'] == 'OPTIMAL'])
    st.metric("✅ Оптимальных", f"{num_optimal}/{num_accounts}")

with col2:
    num_excess = len(health_df[health_df['status'] == 'EXCESS'])
    st.metric("🟠 Избыточных", f"{num_excess}/{num_accounts}")

with col3:
    num_deficit = len(health_df[health_df['status'] == 'DEFICIT'])
    st.metric("🔴 Дефицит", f"{num_deficit}/{num_accounts}")

# График статусов
import plotly.express as px

fig = px.bar(
    health_df.sort_values('status'),
    x='account_id',
    y='current_balance',
    color='status',
    color_discrete_map={'OPTIMAL': '#7b2cbf', 'EXCESS': '#c77dff', 'DEFICIT': '#ff4d6d'},
    title="Остатки по счетам с индикацией статуса"
)

fig.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family="Outfit, Inter, sans-serif", color="#3c096c"),
    title_font=dict(size=16, color="#3c096c", family="Outfit, Inter, sans-serif"),
    xaxis=dict(showgrid=False, linecolor='#ebdfff', title="ID Счета"),
    yaxis=dict(showgrid=True, gridcolor='#f3eeff', linecolor='#ebdfff', title="Текущий баланс ($)")
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# Проблемы
st.markdown("### ⚠️ Требуют внимания")

excess_df = allocator.identify_excess_liquidity()
deficit_df = allocator.identify_deficit_accounts()

if len(excess_df) > 0 or len(deficit_df) > 0:
    st.markdown(f"""
    <div style="background-color: #fff9db; border-left: 5px solid #fab005; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; color: #664d03; font-weight: 500;">
        ⚠️ Обнаружено {len(excess_df) + len(deficit_df)} счетов, требующих оптимизации и внимания.
    </div>
    """, unsafe_allow_html=True)
    
    if len(excess_df) > 0:
        st.markdown(f"""
        <div style="background-color: #fbf8ff; border-left: 5px solid #c77dff; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;">
            <span style="color: #7b2cbf; font-weight: 700;">🟣 {len(excess_df)} счетов с избытком</span> на общую сумму ${excess_df['excess_amount'].sum():,.0f}
        </div>
        """, unsafe_allow_html=True)
    
    if len(deficit_df) > 0:
        st.markdown(f"""
        <div style="background-color: #fff0f3; border-left: 5px solid #ff4d6d; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;">
            <span style="color: #c9184a; font-weight: 700;">🔴 {len(deficit_df)} счетов с дефицитом</span> на общую сумму ${deficit_df['deficit_amount'].sum():,.0f}
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="background-color: #f4fbf7; border-left: 5px solid #2b8a3e; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; color: #2b8a3e; font-weight: 600;">
        ✅ Все счета находятся в оптимальном состоянии!
    </div>
    """, unsafe_allow_html=True)
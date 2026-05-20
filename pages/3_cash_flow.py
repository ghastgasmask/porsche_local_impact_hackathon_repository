"""
Модуль 2: Прогноз денежных потоков
"""

import streamlit as st
from modules.session_data import ensure_session_data
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Прогноз денежных потоков", page_icon=None, layout="wide")
ensure_session_data()

st.markdown("# Cash Flow Predictor")

st.markdown("""
Прогнозирование денежных потоков и выявление кассовых разрывов с учетом задержек платежных систем.
""")

# Получаем данные
accounts_df = st.session_state.accounts_df
transactions_df = st.session_state.transactions_df
scheduled_payments_df = st.session_state.scheduled_payments_df
expected_inflows_df = st.session_state.expected_inflows_df
holidays_df = st.session_state.holidays_df

# Импортируем модуль
from modules.cash_flow_predictor import CashFlowPredictor

# Инициализируем
predictor = CashFlowPredictor(
    accounts_df, 
    transactions_df, 
    scheduled_payments_df,
    expected_inflows_df,
    holidays_df
)

# Получаем прогноз
forecast_df = predictor.predict_daily_cash_flow(days_ahead=30)

# СТАТИСТИКА
st.markdown("## Прогноз на ближайшие 30 дней")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_inflows = forecast_df['inflows'].sum()
    st.metric("Ожидаемые поступления", f"${total_inflows:,.0f}")

with col2:
    total_outflows = forecast_df['outflows'].sum()
    st.metric("Ожидаемые расходы", f"${total_outflows:,.0f}")

with col3:
    net_flow = total_inflows - total_outflows
    st.metric("Чистый поток", f"${net_flow:,.0f}")

with col4:
    current_balance = accounts_df['current_balance'].sum()
    projected = current_balance + net_flow
    st.metric("Прогноз баланса", f"${projected:,.0f}")

st.divider()

# ГРАФИК ПРОГНОЗА
st.markdown("## График денежных потоков")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=forecast_df['date'],
    y=forecast_df['inflows'],
    name='Поступления',
    mode='lines+markers',
    line=dict(color='green', width=2)
))

fig.add_trace(go.Scatter(
    x=forecast_df['date'],
    y=forecast_df['outflows'],
    name='Расходы',
    mode='lines+markers',
    line=dict(color='red', width=2)
))

fig.add_trace(go.Scatter(
    x=forecast_df['date'],
    y=forecast_df['net_flow'],
    name='Чистый поток',
    mode='lines+markers',
    line=dict(color='blue', width=3, dash='dash')
))

fig.update_layout(
    title="Прогноз денежных потоков",
    xaxis_title="Дата",
    yaxis_title="Сумма ($)",
    hovermode='x unified',
    height=500
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ВКЛАДКИ
tab1, tab2, tab3 = st.tabs(["Кассовые разрывы", "Задержки клиринга", "Еженедельный прогноз"])

with tab1:
    st.markdown("### Анализ кассовых разрывов")
    
    gaps_df = predictor.identify_cash_gaps(days_ahead=30, accounts_df=accounts_df)
    
    if len(gaps_df) > 0:
        st.error(f"⚠️ АЛО! ВНИМАНИЕ! Обнаружено **{len(gaps_df)}** потенциальных кассовых разрывов!")
        
        display_gaps = gaps_df.copy()
        display_gaps['forecasted_balance'] = display_gaps['forecasted_balance'].apply(lambda x: f"${x:,.2f}")
        display_gaps['gap_amount'] = display_gaps['gap_amount'].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(display_gaps, hide_index=True, use_container_width=True)
        
        # График разрывов
        fig_gaps = px.bar(
            gaps_df,
            x='date',
            y='gap_amount',
            color='severity',
            color_discrete_map={'CRITICAL': 'red', 'WARNING': 'orange'},
            title="Величина кассовых разрывов"
        )
        st.plotly_chart(fig_gaps, use_container_width=True)
        
        # Решения
        st.markdown("### Предлагаемые решения")
        solutions_df = predictor.generate_gap_solutions(gaps_df)
        
        for _, solution in solutions_df.iterrows():
            if solution['priority'] == 1:
                st.error(f"""
                **🔴 КРИТИЧЕСКОЕ ДЕЙСТВИЕ**
                - Дата разрыва: **{solution['gap_date']}**
                - Требуется: **${solution['gap_amount']:,.0f}**
                - Действие: {solution['action']}
                """)
            else:
                st.warning(f"""
                **🟠 РЕКОМЕНДУЕМОЕ ДЕЙСТВИЕ**
                - Дата разрыва: **{solution['gap_date']}**
                - Требуется: **${solution['gap_amount']:,.0f}**
                - Действие: {solution['action']}
                """)
    else:
        st.success("✅ Кассовых разрывов не обнаружено!")

with tab2:
    st.markdown("### Анализ задержек платежных систем")
    
    delays_df = predictor.analyze_clearing_delays()
    
    if len(delays_df) > 0:
        display_delays = delays_df.copy()
        display_delays['total_in_transit'] = display_delays['total_in_transit'].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(display_delays, hide_index=True, use_container_width=True)
        
        fig_delays = px.bar(
            delays_df,
            x='payment_system',
            y='total_in_transit',
            title="Деньги 'в пути' по платежным системам",
            color='avg_delay_days',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig_delays, use_container_width=True)

with tab3:
    st.markdown("### Еженедельный прогноз")
    
    weekly_df = predictor.get_weekly_forecast_summary()
    
    fig_weekly = go.Figure()
    
    fig_weekly.add_trace(go.Bar(
        x=weekly_df['week_label'],
        y=weekly_df['inflows'],
        name='Поступления',
        marker_color='green'
    ))
    
    fig_weekly.add_trace(go.Bar(
        x=weekly_df['week_label'],
        y=weekly_df['outflows'],
        name='Расходы',
        marker_color='red'
    ))
    
    fig_weekly.update_layout(
        title="Еженедельный прогноз потоков",
        barmode='group',
        height=400
    )
    
    st.plotly_chart(fig_weekly, use_container_width=True)
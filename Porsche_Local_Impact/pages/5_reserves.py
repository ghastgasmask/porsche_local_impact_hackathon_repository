"""
Модуль 4: Оптимизация резервов
"""

import streamlit as st
from modules.session_data import ensure_session_data
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Оптимизация резервов", page_icon=None, layout="wide")
ensure_session_data()

st.markdown("# Reserve Optimizer")

st.markdown("""
Оптимизация резервов ликвидности на основе статистического анализа. Не присутсвует ML.
""")

# Получаем данные
accounts_df = st.session_state.accounts_df
transactions_df = st.session_state.transactions_df
scheduled_payments_df = st.session_state.scheduled_payments_df
expected_inflows_df = st.session_state.expected_inflows_df

# Импортируем из modules/
from modules.reserve_optimizer import ReserveOptimizer

# инциализация
optimizer = ReserveOptimizer(accounts_df, transactions_df, scheduled_payments_df, expected_inflows_df)

# оценка
efficiency = optimizer.calculate_reserve_efficiency_score()

st.markdown("### Общая оценка эффективности")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Оценка", f"{efficiency['score']:.1f}/100")

with col2:
    st.metric("✅ Оптимальных", efficiency['num_optimal'])

with col3:
    st.metric("🟠 Избыточных", efficiency['num_excess'])

with col4:
    st.metric("🔴 Дефицит", efficiency['num_deficit'])

st.progress(efficiency['score'] / 100)

st.divider()

# ВКЛАДКИ
tab1, tab2, tab3, tab4 = st.tabs([
    "Анализ резервов",
    "Test (bugged)",
    "Стресс-тесты",
    "Проекция доходности"
])

with tab1:
    st.markdown("### Сравнение текущих и оптимальных резервов")
    
    analysis_df = optimizer.analyze_current_vs_optimal_reserves()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=analysis_df['account_id'],
        y=analysis_df['current_balance'],
        name='Текущий баланс',
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        x=analysis_df['account_id'],
        y=analysis_df['optimal_reserve'],
        name='Оптимальный резерв',
        marker_color='orange'
    ))
    
    fig.update_layout(
        title="Текущий баланс vs Оптимальный резерв",
        barmode='group',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Таблица
    display_analysis = analysis_df.copy()
    display_analysis['current_balance'] = display_analysis['current_balance'].apply(lambda x: f"${x:,.2f}")
    display_analysis['optimal_reserve'] = display_analysis['optimal_reserve'].apply(lambda x: f"${x:,.2f}")
    display_analysis['difference'] = display_analysis['difference'].apply(lambda x: f"${x:,.2f}")
    display_analysis['difference_pct'] = display_analysis['difference_pct'].apply(lambda x: f"{x:+.1f}%")
    
    st.dataframe(display_analysis, hide_index=True, use_container_width=True)

with tab2:
    st.markdown("Test")

with tab3:
    st.markdown("### Стресс-тестирование")
    
    scenario = st.selectbox(
        "Выберите сценарий:",
        ['mild', 'moderate', 'severe'],
        format_func=lambda x: {'mild': '🟢 Мягкий', 'moderate': '🟠 Умеренный', 'severe': '🔴 Жесткий'}[x]
    )
    
    stress_df = optimizer.stress_test_reserves(scenario=scenario)
    
    num_sufficient = len(stress_df[stress_df['is_sufficient']])
    num_insufficient = len(stress_df[~stress_df['is_sufficient']])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("✅ Устойчивых счетов", num_sufficient)
    
    with col2:
        st.metric("⚠️ Недостаточных", num_insufficient, delta_color="inverse")
    
    # График
    fig_stress = go.Figure()
    
    fig_stress.add_trace(go.Bar(
        x=stress_df['account_id'],
        y=stress_df['current_balance'],
        name='Текущий баланс',
        marker_color='lightblue'
    ))
    
    fig_stress.add_trace(go.Bar(
        x=stress_df['account_id'],
        y=stress_df['stressed_reserve'],
        name='Резерв в стрессе',
        marker_color='red'
    ))
    
    fig_stress.update_layout(barmode='group', height=400)
    st.plotly_chart(fig_stress, use_container_width=True)

with tab4:
    st.markdown("### Проекция доходности")
    
    excess_info = optimizer.calculate_total_excess_reserves()
    
    if excess_info['can_free_up'] > 0:
        projection_df = optimizer.project_reserve_impact(months=12)
        
        fig_projection = go.Figure()
        
        fig_projection.add_trace(go.Scatter(
            x=projection_df['month'],
            y=projection_df['cumulative_income'],
            mode='lines+markers',
            name='Накопительный доход',
            line=dict(color='green', width=3),
            fill='tozeroy'
        ))
        
        fig_projection.update_layout(
            title="Прогноз доходности на 12 месяцев",
            height=400
        )
        
        st.plotly_chart(fig_projection, use_container_width=True)
        
        # Итоговые метрики
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Годовой доход", f"${excess_info['yearly_income']:,.0f}")
        
        with col2:
            st.metric("ROI", f"{excess_info['roi_percentage']}%")
    else:
        st.info("Нет избыточных резервов для высвобождения.")
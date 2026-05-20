"""
Модуль 1: Перераспределение ликвидности
"""

import streamlit as st
from modules.session_data import ensure_session_data
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Перераспределение ликвидности", page_icon=None, layout="wide")
ensure_session_data()

st.markdown("# Smart Cash Allocator")

st.markdown("""
Интеллектуальное перераспределение ликвидности между счетами компании.
""")

# Получаем данные
accounts_df = st.session_state.accounts_df
transactions_df = st.session_state.transactions_df
scheduled_payments_df = st.session_state.scheduled_payments_df

# Импортируем модуль
from modules.cash_allocator import SmartCashAllocator

# Инициализируем
allocator = SmartCashAllocator(accounts_df, transactions_df, scheduled_payments_df)

# Получаем статус
health_df = allocator.get_account_health_status()

# ОСНОВНАЯ СТАТИСТИКА
st.markdown("## Общая статистика по счетам")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_balance = accounts_df['current_balance'].sum()
    st.metric("Общий баланс", f"${total_balance:,.0f}")

with col2:
    num_accounts = len(accounts_df)
    st.metric("Всего счетов", num_accounts)

with col3:
    num_optimal = len(health_df[health_df['status'] == 'OPTIMAL'])
    st.metric("✅ Оптимальных", num_optimal, delta=f"{(num_optimal/num_accounts*100):.0f}%")

with col4:
    num_problems = len(health_df[health_df['status'].isin(['EXCESS', 'DEFICIT', 'CRITICAL'])])
    st.metric("⚠️ Требуют внимания", num_problems, delta=f"{(num_problems/num_accounts*100):.0f}%", delta_color="inverse")

st.divider()

# ЗДОРОВЬЕ СЧЕТОВ
st.markdown("## Здоровье счетов")

fig = px.bar(
    health_df.sort_values('status'),
    x='account_id',
    y='current_balance',
    color='status',
    color_discrete_map={'OPTIMAL': 'green', 'EXCESS': 'orange', 'DEFICIT': 'red'},
    title="Остатки по счетам с индикацией статуса",
    labels={'current_balance': 'Баланс ($)', 'account_id': 'Счет'}
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ВКЛАДКИ
tab1, tab2, tab3 = st.tabs(["Избыточная ликвидность", "Дефицит ликвидности", "Рекомендации"])

with tab1:
    st.markdown("### Счета с избыточной ликвидностью")
    
    excess_df = allocator.identify_excess_liquidity()
    
    if len(excess_df) > 0:
        st.warning(f"Найдено **{len(excess_df)}** счетов с избыточной ликвидностью")
        
        display_excess = excess_df.copy()
        display_excess['current_balance'] = display_excess['current_balance'].apply(lambda x: f"${x:,.2f}")
        display_excess['required_balance'] = display_excess['required_balance'].apply(lambda x: f"${x:,.2f}")
        display_excess['excess_amount'] = display_excess['excess_amount'].apply(lambda x: f"${x:,.2f}")
        display_excess['excess_percentage'] = display_excess['excess_percentage'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(display_excess, hide_index=True, use_container_width=True)
        
        # График
        fig_excess = px.bar(
            excess_df,
            x='account_id',
            y='excess_amount',
            color='currency',
            title="Сумма избыточной ликвидности",
            labels={'excess_amount': 'Избыток ($)', 'account_id': 'Счет'}
        )
        st.plotly_chart(fig_excess, use_container_width=True)
    else:
        st.success("✅ Избыточной ликвидности не обнаружено!")

with tab2:
    st.markdown("### Счета с дефицитом ликвидности")
    
    deficit_df = allocator.identify_deficit_accounts()
    
    if len(deficit_df) > 0:
        st.error(f"Найдено **{len(deficit_df)}** счетов с дефицитом ликвидности")
        
        display_deficit = deficit_df.copy()
        display_deficit['current_balance'] = display_deficit['current_balance'].apply(lambda x: f"${x:,.2f}")
        display_deficit['required_balance'] = display_deficit['required_balance'].apply(lambda x: f"${x:,.2f}")
        display_deficit['deficit_amount'] = display_deficit['deficit_amount'].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(display_deficit, hide_index=True, use_container_width=True)
        
        # График
        fig_deficit = px.bar(
            deficit_df,
            x='account_id',
            y='deficit_amount',
            color='urgency',
            color_discrete_map={'CRITICAL': 'red', 'WARNING': 'orange'},
            title="Дефицит ликвидности",
            labels={'deficit_amount': 'Дефицит ($)', 'account_id': 'Счет'}
        )
        st.plotly_chart(fig_deficit, use_container_width=True)
    else:
        st.success("✅ Дефицита ликвидности не обнаружено!")

with tab3:
    st.markdown("### Рекомендации по оптимизации")
    
    recommendations_df = allocator.generate_reallocation_recommendations()
    
    if len(recommendations_df) > 0:
        st.info(f"Система сгенерировала **{len(recommendations_df)}** рекомендаций")
        
        for priority in sorted(recommendations_df['priority'].unique()):
            priority_recs = recommendations_df[recommendations_df['priority'] == priority]
            
            priority_labels = {
                1: "🔴 КРИТИЧНО",
                2: "🟠 ВАЖНО",
                3: "🟢 РЕКОМЕНДУЕТСЯ"
            }
            
            with st.expander(f"{priority_labels.get(priority)} ({len(priority_recs)} действий)", expanded=(priority == 1)):
                for idx, rec in priority_recs.iterrows():
                    if rec['action'] == 'TRANSFER':
                        st.markdown(f"""
                        **Перевод #{idx+1}**
                        - Со счета: `{rec['from_account']}`
                        - На счет: `{rec['to_account']}`
                        - Сумма: **{rec['currency']} {rec['amount']:,.2f}**
                        - Причина: {rec['reason']}
                        """)
                    elif rec['action'] == 'INVEST':
                        st.markdown(f"""
                        **Инвестирование #{idx+1}**
                        - Со счета: `{rec['from_account']}`
                        - Сумма: **{rec['currency']} {rec['amount']:,.2f}**
                        - Причина: {rec['reason']}
                        """)
    else:
        st.success("✅ Рекомендаций нет. Распределение ликвидности оптимально!!!!!!!!!")

st.divider()

# ЭФФЕКТ
st.markdown("## Потенциальный эффект от оптимизации")

impact = allocator.calculate_optimization_impact()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Замороженная ликвидность",
        f"${impact['total_excess']:,.0f}"
    )

with col2:
    st.metric(
        "Доход в месяц (под 4%)",
        f"${impact['potential_monthly_income']:,.0f}"
    )

with col3:
    st.metric(
        "Доход в год",
        f"${impact['potential_yearly_income']:,.0f}"
    )

if impact['total_excess'] > 0:
    st.warning(f"""
    ⚠️ То есть, на данный момент ${impact['total_excess']:,.0f} не используется эффективно.
    Если оптимизировать компания может получать ${impact['potential_yearly_income']:,.0f}
    дополнительного дохода в год
    """)
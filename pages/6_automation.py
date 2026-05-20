"""
Модуль 5: Автоматизация и алерты
"""

import streamlit as st
from modules.session_data import ensure_session_data
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Автоматизация и алерты", page_icon=None, layout="wide")
ensure_session_data()

st.markdown("# Automated Treasury Control Center")

st.markdown("""
Система алертов, автоматических действий и рил-тайм мониторинга
""")

# Получаем данные
accounts_df = st.session_state.accounts_df
transactions_df = st.session_state.transactions_df
scheduled_payments_df = st.session_state.scheduled_payments_df
expected_inflows_df = st.session_state.expected_inflows_df

# Принудительная перезагрузка модулей для Streamlit, чтобы применить изменения в коде
import sys
import importlib
if 'modules.automation_center' in sys.modules:
    importlib.reload(sys.modules['modules.automation_center'])
if 'modules.action_executor' in sys.modules:
    importlib.reload(sys.modules['modules.action_executor'])

# Импортируем
from modules.automation_center import AutomationCenter

# Сначала инициализируем AutomationCenter
automation = AutomationCenter(
    accounts_df,
    transactions_df,
    scheduled_payments_df,
    expected_inflows_df
)

# Проверяем состояние авто-режима до отображения метрик здоровья
auto_mode_active = st.session_state.get("auto_mode", False)
automation_results = []

if auto_mode_active:
    automation_results = automation.execute_automated_actions(enable_auto=True, accounts_df=accounts_df)
    # Переинициализируем AutomationCenter, чтобы обновить состояние балансов для верхних показателей здоровья
    automation = AutomationCenter(
        accounts_df,
        transactions_df,
        scheduled_payments_df,
        expected_inflows_df
    )

# Статус системы
health_status = automation.get_system_health_status()

st.markdown("### Статус системы")

col1, col2, col3, col4 = st.columns(4)

status_emoji = {'OK': '✅', 'WARNING': '⚠️', 'CRITICAL': '🔴'}

with col1:
    st.metric(
        "Статус",
        f"{status_emoji[health_status['overall_status']]} {health_status['overall_status']}"
    )

with col2:
    st.metric("🔴 Критичные", health_status['num_critical_alerts'], delta_color="inverse")

with col3:
    st.metric("⚠️ Предупреждения", health_status['num_warnings'])

with col4:
    total_balance = accounts_df['current_balance'].sum()
    st.metric("Общий баланс", f"${total_balance:,.0f}")

st.divider()

# Здоровье компонентов
st.markdown("### Здоровье компонентов")

components = health_status['components']

col1, col2, col3, col4 = st.columns(4)

components_config = [
    ('liquidity', 'Ликвидность', col1),
    ('cash_flow', 'Денежные потоки', col2),
    ('reserves', 'Резервы', col3),
    ('activity', 'Активность', col4)
]

for key, label, col in components_config:
    with col:
        comp = components[key]
        status_color = {
            'GREAT BRO!': 'green',
            'ALRIGHT': 'orange',
            'WARNING!!!': 'orange',
            'CRITICAL': 'red'
        }
        
        st.markdown(f"**{label}**")
        st.progress(comp['score'] / 100)
        st.markdown(f"<p style='text-align:center; color:{status_color.get(comp['status'], 'gray')}'>{comp['status']} ({comp['score']}/100)</p>", unsafe_allow_html=True)

st.divider()

# ВКЛАДКИ
tab1, tab2, tab3, tab4 = st.tabs([
    "Алерты",
    "🤖 Автоматизация",
    "Dashboard",
    "Отчеты"
])

with tab1:
    st.markdown("### Активные алерты")
    
    alerts_df = automation.generate_real_time_alerts()
    
    if len(alerts_df) > 0:
        severity_filter = st.multiselect(
            "Фильтр:",
            ['CRITICAL', 'WARNING', 'INFO'],
            default=['CRITICAL', 'WARNING', 'INFO']
        )
        
        filtered_alerts = alerts_df[alerts_df['severity'].isin(severity_filter)]
        
        st.info(f"Всего: **{len(filtered_alerts)}** алертов")
        
        for severity in ['CRITICAL', 'WARNING', 'INFO']:
            severity_alerts = filtered_alerts[filtered_alerts['severity'] == severity]
            
            if len(severity_alerts) == 0:
                continue
            
            emoji = {'CRITICAL': '🔴', 'WARNING': '⚠️', 'INFO': ''}[severity]
            
            with st.expander(f"{emoji} {severity} ({len(severity_alerts)})", expanded=(severity == 'CRITICAL')):
                for idx, alert in severity_alerts.iterrows():
                    st.markdown(f"""
                    **{alert['type']}**
                    - Счет: `{alert['account']}`
                    - {alert['message']}
                    - Рекомендация: {alert['suggested_action']}
                    """)
                    st.divider()
    else:
        st.success("✅ Активных алертов нет!")

with tab2:
    st.markdown("### Автоматические действия")
    
    # Тумблер для включения/выключения автоматизации
    auto_mode = st.toggle("Включить автоматизацию", key="auto_mode", value=False)
    
    if auto_mode:
        if automation_results:
            st.success("🤖 Автоматические действия успешно выполнены!")
            
            # Статистика
            success_count = sum(1 for r in automation_results if r['success'])
            failed_count = sum(1 for r in automation_results if not r['success'])
            
            # Подсчет переведенных сумм по валютам
            transferred_sums = {}
            for r in automation_results:
                if r['success']:
                    curr = r['currency']
                    transferred_sums[curr] = transferred_sums.get(curr, 0.0) + r['amount']
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Успешно выполнено", success_count)
            with col2:
                st.metric("Ошибки / Превышен лимит", failed_count)
                
            if transferred_sums:
                st.markdown("##### 💵 Итого переведено:")
                for curr, amt in transferred_sums.items():
                    st.write(f"- **{curr}:** {amt:,.2f}")
            
            st.divider()
            st.markdown("#### Отчет о выполненных действиях")
            
            for r in automation_results:
                status_emoji = "✅" if r['success'] else "❌"
                status_text = "Успешно" if r['success'] else "Отклонено/Ошибка"
                
                st.markdown(f"""
                **ID Действия:** `{r['action_id']}` ({r['type']})
                - **Направление:** `{r['from_account']}` ➔ `{r['to_account']}`
                - **Сумма:** {r['currency']} {r['amount']:,.2f}
                - **Статус:** {status_emoji} {status_text}
                - **Детали:** {r['message']}
                """)
                st.divider()
        else:
            st.info("🤖 Активных автоматических действий на данный момент нет.")
    else:
        # Режим рекомендации
        actions_df = automation.create_automated_actions(enable_auto=False)
        
        if len(actions_df) > 0:
            auto_stats = automation.get_automation_statistics()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Доступно для автовыполнения", auto_stats['auto_executable'])
            with col2:
                st.metric("Потенциальная экономия", f"${auto_stats['potential_savings']}")
            
            st.markdown("#### Список рекомендуемых действий (активируйте тумблер для выполнения):")
            for idx, action in actions_df.iterrows():
                exec_status = "Да" if action['auto_executable'] else "Нет (требуется ручное подтверждение из-за лимита)"
                st.markdown(f"""
                **ID:** `{action['action_id']}`
                - **Тип:** {action['type']}
                - **Направление:** `{action['from_account']}` ➔ `{action['to_account']}`
                - **Сумма:** {action['currency']} {action['amount']:,.2f}
                - **Причина:** {action['reason']}
                - **Автовыполнение:** {exec_status}
                - **Текущий статус:** `Ожидает включения автоматизации`
                """)
                st.divider()
        else:
            st.info("Автоматических действий не требуется.")

with tab3:
    st.markdown("### Real-time Dashboard")
    
    if st.button("Обновить", use_container_width=True):
        st.rerun()
    
    # Карта счетов
    account_viz = []
    
    for _, account in accounts_df.iterrows():
        balance = account['current_balance']
        min_balance = account['minimum_balance']
        
        if balance < min_balance:
            status = 'CRITICAL'
        elif balance < min_balance * 1.2:
            status = 'WARNING'
        else:
            status = 'OK'
        
        account_viz.append({
            'account_id': account['account_id'],
            'balance': balance,
            'status': status,
            'currency': account['currency']
        })
    
    viz_df = pd.DataFrame(account_viz)
    
    fig_map = px.scatter(
        viz_df,
        x='account_id',
        y='balance',
        size='balance',
        color='status',
        color_discrete_map={'OK': 'green', 'WARNING': 'orange', 'CRITICAL': 'red'},
        title="Статус балансов по счетам"
    )
    st.plotly_chart(fig_map, use_container_width=True)

with tab4:
    st.markdown("### Ежедневный отчет")
    
    report = automation.generate_daily_report()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Поступления (вчера)", f"${report['summary']['total_inflows']:,.0f}")
    
    with col2:
        st.metric("Расходы (вчера)", f"${report['summary']['total_outflows']:,.0f}")
    
    with col3:
        st.metric("Чистый поток", f"${report['summary']['net_flow']:,.0f}")
    
    st.markdown(f"""
    - **Общий баланс:** ${report['summary']['total_balance']:,.0f}
    - **Критичных проблем:** {report['critical_issues']}
    - **Всего алертов:** {report['active_alerts']}
    """)
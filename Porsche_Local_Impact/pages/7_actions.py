"""
Страница управления действиями и данными
"""

import streamlit as st
from modules.session_data import ensure_session_data
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Управление действиями", page_icon=None, layout="wide")
ensure_session_data()

st.markdown("# Управление действиями и данными")

st.markdown("""
Интерактивное управление операциями: выполнение переводов, резервирования, инвестирования.
Все действия логируются и влияют на данные в системе.
""")

# Импортируем модули
from modules.action_executor import ActionExecutor

# Инициализируем
executor = ActionExecutor()

# Получаем данные
accounts_df = st.session_state.accounts_df.copy()
transactions_df = st.session_state.transactions_df

# ВКЛАДКИ
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Переводы",
    "Резервирование",
    "Инвестирование",
    "История действий",
    "Редактирование данных"
])

# ============================================
# ВКЛАДКА 1: ПЕРЕВОДЫ
# ============================================
with tab1:
    st.markdown("### Выполнить перевод между счетами")
    
    st.info("Выберите счета и сумму для выполнения перевода. Действие будет записано в историю и изменит балансы.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        from_account = st.selectbox(
            "Счет отправителя:",
            accounts_df['account_id'].tolist(),
            key="transfer_from"
        )
        
        from_acc_data = accounts_df[accounts_df['account_id'] == from_account].iloc[0]
        st.metric("Текущий баланс", f"${from_acc_data['current_balance']:,.2f} {from_acc_data['currency']}")
    
    with col2:
        to_account = st.selectbox(
            "Счет получателя:",
            accounts_df['account_id'].tolist(),
            key="transfer_to"
        )
        
        to_acc_data = accounts_df[accounts_df['account_id'] == to_account].iloc[0]
        st.metric("Текущий баланс", f"${to_acc_data['current_balance']:,.2f} {to_acc_data['currency']}")
    
    # Проверка валют
    if from_acc_data['currency'] != to_acc_data['currency']:
        st.error(f"⚠️ Валюты не совпадают! {from_acc_data['currency']} → {to_acc_data['currency']}")
        st.stop()
    
    currency = from_acc_data['currency']
    
    # Форма перевода
    col1, col2 = st.columns(2)
    
    with col1:
        amount = st.number_input(
            "Сумма для перевода:",
            min_value=0.01,
            max_value=from_acc_data['current_balance'],
            step=1000.0,
            key="transfer_amount"
        )
    
    with col2:
        description = st.text_input(
            "Описание перевода:",
            placeholder="Например: Оптимизация ликвидности",
            key="transfer_desc"
        )
    
    # Кнопка выполнить
    if st.button("✅ Выполнить перевод", key="execute_transfer", use_container_width=True):
        result = executor.execute_transfer(
            from_account=from_account,
            to_account=to_account,
            amount=amount,
            currency=currency,
            accounts_df=accounts_df,
            description=description,
            executed_by=st.session_state.get('user_name', 'Пользователь')
        )
        
        if result['success']:
            st.success(result['message'])
            
            # Показываем результат
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                **Счет отправителя: {from_account}**
                - Было: ${from_acc_data['current_balance']:,.2f}
                - Стало: ${result['from_new_balance']:,.2f}
                """)
            
            with col2:
                st.markdown(f"""
                **Счет получателя: {to_account}**
                - Было: ${to_acc_data['current_balance']:,.2f}
                - Стало: ${result['to_new_balance']:,.2f}
                """)
            
            st.info(f"ID действия: `{result['action_id']}`")
            
            # Перезагружаем данные
            st.session_state.accounts_df = accounts_df
            st.rerun()
        else:
            st.error(f"Ошибка: {result['message']}")
    
    st.divider()
    
    # История переводов
    st.markdown("### История последних переводов")
    
    history = executor.get_actions_history(action_type_filter=['TRANSFER'], limit=10)
    
    if len(history) > 0:
        display_history = history.copy()
        display_history['timestamp'] = display_history['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        display_history['amount'] = display_history['amount'].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(
            display_history[[
                'action_id', 'timestamp', 'from_account', 'to_account', 
                'amount', 'currency', 'status', 'description'
            ]],
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("История переводов пуста")

# ============================================
# ВКЛАДКА 2: РЕЗЕРВИРОВАНИЕ
# ============================================
with tab2:
    st.markdown("### Зарезервировать средства")
    
    st.info("Резервирование бронирует средства на счете для критичных платежей.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        reserve_account = st.selectbox(
            "Счет для резервирования:",
            accounts_df['account_id'].tolist(),
            key="reserve_account"
        )
        
        reserve_acc = accounts_df[accounts_df['account_id'] == reserve_account].iloc[0]
        st.metric("Доступно", f"${reserve_acc['current_balance']:,.2f} {reserve_acc['currency']}")
    
    with col2:
        reserve_reason = st.selectbox(
            "Причина резервирования:",
            [
                "Критичный платеж",
                "Страховка кассового разрыва",
                "Плановый платеж партнеру",
                "Выплата зарплаты",
                "Другое"
            ]
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        reserve_amount = st.number_input(
            "Сумма для резервирования:",
            min_value=0.01,
            max_value=reserve_acc['current_balance'],
            step=1000.0,
            key="reserve_amount"
        )
    
    with col2:
        reserve_custom = st.text_input(
            "Дополнительная информация:",
            key="reserve_custom"
        )
    
    if st.button("✅ Зарезервировать", key="execute_reserve", use_container_width=True):
        reason = reserve_reason
        if reserve_custom:
            reason += f" - {reserve_custom}"
        
        result = executor.reserve_funds(
            account_id=reserve_account,
            amount=reserve_amount,
            currency=reserve_acc['currency'],
            reason=reason,
            accounts_df=accounts_df
        )
        
        if result['success']:
            st.success(result['message'])
            st.info(f"ID резервирования: `{result['action_id']}`")
        else:
            st.error(f"Ошибка: {result['message']}")
    
    st.divider()
    
    # История резервирований
    st.markdown("### История резервирований")
    
    history = executor.get_actions_history(action_type_filter=['RESERVE'], limit=10)
    
    if len(history) > 0:
        display_history = history.copy()
        display_history['timestamp'] = display_history['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        display_history['amount'] = display_history['amount'].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(
            display_history[[
                'action_id', 'timestamp', 'from_account', 'amount', 
                'status', 'description'
            ]],
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("История резервирований пуста")

# ============================================
# ВКЛАДКА 3: ИНВЕСТИРОВАНИЕ
# ============================================
with tab3:
    st.markdown("### Инвестировать избыточные средства")
    
    st.info("Вложите избыточные средства под процент. Это уменьшит баланс на счете, но принесет доход.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        invest_account = st.selectbox(
            "Счет для инвестирования:",
            accounts_df['account_id'].tolist(),
            key="invest_account"
        )
        
        invest_acc = accounts_df[accounts_df['account_id'] == invest_account].iloc[0]
        st.metric("Доступно", f"${invest_acc['current_balance']:,.2f} {invest_acc['currency']}")
    
    with col2:
        invest_type = st.selectbox(
            "Тип инвестирования:",
            [
                "Overnight депозит (4%)",
                "Краткосрочный депозит (5%)",
                "Средний депозит (6%)",
                "Долгий депозит (7%)"
            ]
        )
    
    # Парсим годовую ставку
    annual_rate = {
        "Overnight депозит (4%)": 4.0,
        "Краткосрочный депозит (5%)": 5.0,
        "Средний депозит (6%)": 6.0,
        "Долгий депозит (7%)": 7.0
    }[invest_type]
    
    col1, col2 = st.columns(2)
    
    with col1:
        invest_amount = st.number_input(
            "Сумма для инвестирования:",
            min_value=0.01,
            max_value=invest_acc['current_balance'],
            step=1000.0,
            key="invest_amount"
        )
    
    with col2:
        monthly_income = invest_amount * (annual_rate / 100) / 12
        yearly_income = invest_amount * (annual_rate / 100)
        
        st.metric("Доход в месяц", f"${monthly_income:,.2f}")
    
    st.metric("Доход в год", f"${yearly_income:,.2f}")
    
    if st.button("✅ Инвестировать", key="execute_invest", use_container_width=True):
        result = executor.invest_funds(
            account_id=invest_account,
            amount=invest_amount,
            currency=invest_acc['currency'],
            investment_type=invest_type.split('(')[0].strip(),
            annual_rate=annual_rate,
            accounts_df=accounts_df
        )
        
        if result['success']:
            st.success(result['message'])
            st.markdown(f"""
            **Прогноз доходности:**
            - Доход в месяц: ${result['monthly_income']:,.2f}
            - Доход в год: ${result['yearly_income']:,.2f}
            """)
            st.info(f"ID инвестирования: `{result['action_id']}`")
            
            # Перезагружаем
            st.session_state.accounts_df = accounts_df
            st.rerun()
        else:
            st.error(f"Ошибка: {result['message']}")
    
    st.divider()
    
    # История инвестиций
    st.markdown("### История инвестиций")
    
    history = executor.get_actions_history(action_type_filter=['INVEST'], limit=10)
    
    if len(history) > 0:
        display_history = history.copy()
        display_history['timestamp'] = display_history['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        display_history['amount'] = display_history['amount'].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(
            display_history[[
                'action_id', 'timestamp', 'from_account', 'to_account',
                'amount', 'status', 'description'
            ]],
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("История инвестиций пуста")

# ============================================
# ВКЛАДКА 4: ИСТОРИЯ ДЕЙСТВИЙ
# ============================================
with tab4:
    st.markdown("### Полная история действий")
    
    # Фильтры
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.multiselect(
            "Статус:",
            ['EXECUTED', 'ACTIVE', 'RESERVED', 'PENDING'],
            default=['EXECUTED', 'ACTIVE', 'RESERVED']
        )
    
    with col2:
        action_filter = st.multiselect(
            "Тип действия:",
            ['TRANSFER', 'RESERVE', 'INVEST', 'RELEASE_RESERVE'],
            default=['TRANSFER', 'RESERVE', 'INVEST']
        )
    
    with col3:
        limit = st.slider("Показать последних:", 10, 100, 50)
    
    # Получаем историю
    history = executor.get_actions_history(
        status_filter=status_filter if status_filter else None,
        action_type_filter=action_filter if action_filter else None,
        limit=limit
    )
    
    if len(history) > 0:
        # Статистика
        stats = executor.get_statistics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Всего действий", stats['total_actions'])
        
        with col2:
            st.metric("✅ Выполнено", stats['executed'])
        
        with col3:
            st.metric("Переведено", f"${stats['total_transferred']:,.2f}")
        
        with col4:
            st.metric("Инвестировано", f"${stats['total_invested']:,.2f}")
        
        st.divider()
        
        # Таблица
        display_history = history.copy()
        display_history['timestamp'] = display_history['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        display_history['amount'] = display_history['amount'].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(
            display_history,
            hide_index=True,
            use_container_width=True
        )
        
        # График по типам
        fig = px.pie(
            history,
            names='action_type',
            title="Распределение действий по типам"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Действий не найдено по выбранным фильтрам")

# ============================================
# ВКЛАДКА 5: РЕДАКТИРОВАНИЕ ДАННЫХ
# ============================================
with tab5:
    st.markdown("### Редактирование данных счетов")
    
    st.warning("""
    ⚠️ Осторожно! Изменения здесь влияют на все остальные страницы приложения.
    Все изменения сохраняются в CSV файлы.
    """)
    
    # Выбор файла для редактирования
    file_to_edit = st.selectbox(
        "Выберите файл для редактирования:",
        [
            "Остатки на счетах (accounts_balances.csv)",
            "Запланированные платежи (scheduled_payments.csv)",
            "Ожидаемые поступления (expected_inflows.csv)"
        ]
    )
    
    file_map = {
        "Остатки на счетах (accounts_balances.csv)": 'data/accounts_balances.csv',
        "Запланированные платежи (scheduled_payments.csv)": 'data/scheduled_payments.csv',
        "Ожидаемые поступления (expected_inflows.csv)": 'data/expected_inflows.csv'
    }
    
    filepath = file_map[file_to_edit]
    
    # Загружаем данные
    if file_to_edit == "Остатки на счетах (accounts_balances.csv)":
        edit_df = accounts_df.copy()
    else:
        edit_df = pd.read_csv(filepath)
    
    st.markdown(f"#### Редактирование: {file_to_edit}")
    
    # Редактируемая таблица
    edited_df = st.data_editor(
        edit_df,
        use_container_width=True,
        height=400,
        key=f"editor_{file_to_edit}"
    )
    
    # Кнопка сохранения
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Сохранить изменения", use_container_width=True):
            edited_df.to_csv(filepath, index=False)
            
            # Обновляем session_state
            if file_to_edit == "Остатки на счетах (accounts_balances.csv)":
                st.session_state.accounts_df = edited_df
            
            st.success("✅ Изменения сохранены!")
            st.info("Перезагрузите страницы для отражения изменений")
    
    with col2:
        if st.button("Отменить изменения", use_container_width=True):
            st.rerun()
    
    # Сравнение до и после
    if not edit_df.equals(edited_df):
        st.markdown("#### Изменения")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Было:**")
            st.dataframe(edit_df, use_container_width=True)
        
        with col2:
            st.markdown("**Стало:**")
            st.dataframe(edited_df, use_container_width=True)
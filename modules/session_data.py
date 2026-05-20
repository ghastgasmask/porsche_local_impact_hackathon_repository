# Загрузка данных в session_state для всех страниц Streamlit

import streamlit as st
import pandas as pd

SESSION_KEYS = (
    "accounts_df",
    "transactions_df",
    "scheduled_payments_df",
    "expected_inflows_df",
    "holidays_df",
)


@st.cache_data
def _load_csv_data():
    accounts = pd.read_csv("data/accounts_balances.csv")
    transactions = pd.read_csv("data/transactions_history.csv")
    scheduled_payments = pd.read_csv("data/scheduled_payments.csv")
    expected_inflows = pd.read_csv("data/expected_inflows.csv")
    holidays = pd.read_csv("data/holidays_calendar.csv")
    return accounts, transactions, scheduled_payments, expected_inflows, holidays


def ensure_session_data() -> None:
    # Заполняет session_state если страницу открыли напрямую, без app.py
    if all(key in st.session_state for key in SESSION_KEYS):
        return

    (
        accounts_df,
        transactions_df,
        scheduled_payments_df,
        expected_inflows_df,
        holidays_df,
    ) = _load_csv_data()

    st.session_state.accounts_df = accounts_df
    st.session_state.transactions_df = transactions_df
    st.session_state.scheduled_payments_df = scheduled_payments_df
    st.session_state.expected_inflows_df = expected_inflows_df
    st.session_state.holidays_df = holidays_df

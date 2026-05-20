# Сборщик контекста
# Краткие сводки по реальным данным для системного промпта ЛЛМки
# Маленькие счета включаются целиком
# Большие (транзакции) только статистика

import streamlit as st
import pandas as pd

from modules.session_data import ensure_session_data


def build_data_context() -> str:
    ensure_session_data()
    # Собирает текстовую сводку    
    # Подставляется в системный промпт чтобы LLM отвечал на реальных цифрах
    sections = []
    sections.append("=" * 60)
    sections.append("LIVE DATA SNAPSHOT (from the current system)")
    sections.append("Use this data to answer user questions accurately.")
    sections.append("=" * 60)

    # Счета: полная таблица (~20 строк)
    if "accounts_df" in st.session_state:
        df = st.session_state.accounts_df
        sections.append(_build_accounts_context(df))

    # Транзакции: статистика (82K+ строк im tired boss)
    if "transactions_df" in st.session_state:
        df = st.session_state.transactions_df
        sections.append(_build_transactions_context(df))

    # Запланированные платежи: сводка
    if "scheduled_payments_df" in st.session_state:
        df = st.session_state.scheduled_payments_df
        sections.append(_build_payments_context(df))

    # Ожидаемые поступления: сводка
    if "expected_inflows_df" in st.session_state:
        df = st.session_state.expected_inflows_df
        sections.append(_build_inflows_context(df))

    return "\n\n".join(sections)


def _build_accounts_context(df: pd.DataFrame) -> str:
    # Полная таблица счетов достаточно мала чтобы включить целиком
    lines = ["ACCOUNTS DATA (full table):"]
    lines.append(f"Total accounts: {len(df)}")
    lines.append(f"Total balance across all accounts: ${df['current_balance'].sum():,.2f}")
    lines.append("")

    # Каждый счёт в читаемом виде
    for _, row in df.iterrows():
        balance = row['current_balance']
        minimum = row['minimum_balance']
        optimal = row['optimal_balance']
        liquidity_ratio = balance / minimum if minimum > 0 else float('inf')
        lines.append(
            f"  • {row['account_id']} | {row['bank_name']} | {row['account_type']} | "
            f"{row['currency']} | Balance: ${balance:,.2f} | "
            f"Min: ${minimum:,.2f} | Optimal: ${optimal:,.2f} | "
            f"Liquidity Ratio: {liquidity_ratio:.2f}x"
        )

    # Счета ниже мин баланса
    below_min = df[df['current_balance'] < df['minimum_balance']]
    if not below_min.empty:
        lines.append("")
        lines.append("⚠️ ACCOUNTS BELOW MINIMUM BALANCE:")
        for _, row in below_min.iterrows():
            shortfall = row['minimum_balance'] - row['current_balance']
            lines.append(
                f"  {row['account_id']} ({row['bank_name']}) — "
                f"Balance: ${row['current_balance']:,.2f}, "
                f"Minimum: ${row['minimum_balance']:,.2f}, "
                f"Shortfall: ${shortfall:,.2f}"
            )

    # Счета ниже оптимума праймуса
    below_opt = df[
        (df['current_balance'] >= df['minimum_balance']) &
        (df['current_balance'] < df['optimal_balance'])
    ]
    if not below_opt.empty:
        lines.append("")
        lines.append("ACCOUNTS BELOW OPTIMAL BALANCE (but above minimum):")
        for _, row in below_opt.iterrows():
            lines.append(
                f"  • {row['account_id']} ({row['bank_name']}) — "
                f"Balance: ${row['current_balance']:,.2f}, "
                f"Optimal: ${row['optimal_balance']:,.2f}"
            )

    return "\n".join(lines)


def _build_transactions_context(df: pd.DataFrame) -> str:
    # Статистика по транзакциям 
    lines = ["TRANSACTIONS SUMMARY:"]
    lines.append(f"Total transactions: {len(df):,}")
    lines.append(f"Total transaction volume: ${df['amount'].sum():,.2f}")
    lines.append(f"Average transaction: ${df['amount'].mean():,.2f}")
    lines.append(f"Largest transaction: ${df['amount'].max():,.2f}")

    # По направлению
    if 'direction' in df.columns:
        for direction in df['direction'].unique():
            subset = df[df['direction'] == direction]
            lines.append(
                f"  {direction.title()}: {len(subset):,} transactions, "
                f"total ${subset['amount'].sum():,.2f}"
            )

    # По статусу
    if 'status' in df.columns:
        lines.append("  Status breakdown:")
        for status, count in df['status'].value_counts().items():
            lines.append(f"    • {status}: {count:,}")

    # По валюте
    if 'currency' in df.columns:
        lines.append("  Currency breakdown:")
        for currency, group in df.groupby('currency'):
            lines.append(
                f"    • {currency}: {len(group):,} txns, "
                f"total ${group['amount'].sum():,.2f}"
            )

    # По платежам
    if 'payment_system' in df.columns:
        lines.append("  Payment system breakdown:")
        for system, count in df['payment_system'].value_counts().items():
            lines.append(f"    • {system}: {count:,}")

    return "\n".join(lines)


def _build_payments_context(df: pd.DataFrame) -> str:
    # Сводка по  платежам
    lines = ["SCHEDULED PAYMENTS SUMMARY:"]
    lines.append(f"Total scheduled payments: {len(df)}")
    lines.append(f"Total amount due: ${df['amount'].sum():,.2f}")

    # приоритет
    if 'priority' in df.columns:
        lines.append("  By priority:")
        for priority, group in df.groupby('priority'):
            lines.append(
                f"    • {priority}: {len(group)} payments, "
                f"total ${group['amount'].sum():,.2f}"
            )

    # По валюте
    if 'currency' in df.columns:
        lines.append("  By currency:")
        for currency, group in df.groupby('currency'):
            lines.append(
                f"    • {currency}: {len(group)} payments, "
                f"total ${group['amount'].sum():,.2f}"
            )

    # Платежи которые можно отложить
    if 'can_be_delayed' in df.columns:
        delayable = df[df['can_be_delayed'].astype(str).str.lower() == 'true']
        lines.append(
            f"  Delayable payments: {len(delayable)} "
            f"(${delayable['amount'].sum():,.2f})"
        )

    return "\n".join(lines)


def _build_inflows_context(df: pd.DataFrame) -> str:
    # Сводка по поступлениям
    lines = ["EXPECTED INFLOWS SUMMARY:"]
    lines.append(f"Total expected inflows: {len(df)}")
    lines.append(f"Total expected amount: ${df['amount'].sum():,.2f}")

    # По статусу
    if 'status' in df.columns:
        lines.append("  By status:")
        for status, group in df.groupby('status'):
            lines.append(
                f"    • {status}: {len(group)} inflows, "
                f"total ${group['amount'].sum():,.2f}"
            )

    # По валюте
    if 'currency' in df.columns:
        lines.append("  By currency:")
        for currency, group in df.groupby('currency'):
            lines.append(
                f"    • {currency}: {len(group)} inflows, "
                f"total ${group['amount'].sum():,.2f}"
            )

    return "\n".join(lines)

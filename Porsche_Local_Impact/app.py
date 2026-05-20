"""
Главный файл приложения Streamlit
"""

import streamlit as st
import pandas as pd 
import os
from modules.action_executor import ActionExecutor
from modules.session_data import ensure_session_data

#  логи
if not os.path.exists('data/actions_log.csv'):
    with open('data/actions_log.csv', 'w') as f:
        f.write("action_id,timestamp,action_type,status,from_account,to_account,amount,currency,description,executed_by,notes\n")
executor = ActionExecutor()

# Настройка страницы
st.set_page_config(
    page_title="Система управления ликвидностью",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Кастомный CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #5a189a;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f8f5fe;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #7b2cbf;
    }
    .date-card {
        background: linear-gradient(135deg, #ffffff 0%, #fcfaff 100%);
        border: 1px solid #ebdfff;
        border-left: 5px solid #7b2cbf;
        border-radius: 10px;
        padding: 1.2rem;
        margin: 1.5rem auto;
        box-shadow: 0 4px 12px rgba(123, 44, 191, 0.05);
        max-width: 450px;
        text-align: center;
    }
    .date-card-title {
        font-size: 0.85rem;
        font-weight: bold;
        color: #7b2cbf;
        text-transform: uppercase;
        letter-spacing: 0.05rem;
        margin-bottom: 0.4rem;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 0.5rem;
    }
    .date-card-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #240046;
        line-height: 1.2;
    }
    .date-card-note {
        font-size: 0.8rem;
        color: #9d4edd;
        font-style: italic;
        margin-top: 0.6rem;
        border-top: 1px solid #ebdfff;
        padding-top: 0.4rem;
    }
</style>
""", unsafe_allow_html=True)

# Загрузка данных в session_state
ensure_session_data()

# Отображаем логотип с помощью стандартного метода Streamlit
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.image("images/porsche_logo.png", use_container_width=True)

# Красивый центрированный баннер с приветствием
st.markdown("""
<div style="text-align: center; padding: 1.5rem 1rem; margin-top: 0.5rem; margin-bottom: 2rem; background: linear-gradient(135deg, #f8f6ff 0%, #f0ebff 100%); border-radius: 15px; border: 1px solid #e3d9ff; box-shadow: 0 8px 32px rgba(123, 44, 191, 0.06);">
    <h1 style="color: #3c096c; font-size: 2.8rem; font-weight: 850; margin: 0; line-height: 1.2; font-family: 'Outfit', 'Inter', sans-serif;">Total Liquidity Control</h1>
    <p style="color: #7b2cbf; font-size: 1.2rem; margin-top: 0.5rem; margin-bottom: 1.5rem; font-weight: 500;">Система интеллектуального контроля и прогнозирования ликвидности</p>
    <div style="display: inline-block; padding: 0.4rem 1.2rem; background-color: #ffffff; border-radius: 50px; border: 1px solid #ebdfff; box-shadow: 0 2px 8px rgba(123, 44, 191, 0.04);">
        <span style="color: #5a189a; font-weight: 700; font-size: 0.95rem;">Команда Porsche</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Красивая дата и примечание
st.markdown("""
<div class="date-card">
    <div class="date-card-title">Текущая дата в системе</div>
    <div class="date-card-value">20 мая 2026 г.</div>
    <div class="date-card-note">
        * (Это фиксированная системная дата для хакатона!! Внутри кода все даты рассчитываются динамически)
    </div>
</div>
""", unsafe_allow_html=True)



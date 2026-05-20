import streamlit as st

def init_memory():
    # Инициализирует память чата в session_state Streamlit
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

def add_message(role, content):
    # Добавляет сообщение в память
    st.session_state.chat_history.append({"role": role, "content": content})

def get_messages():
    # Возвращает все сообщения в формате для LLM API
    return st.session_state.chat_history

def clear_memory():
    # Очищает историю диалога
    st.session_state.chat_history = []

import streamlit as st
from modules.session_data import ensure_session_data

# Модульная архитектура LLM
from modules.llm.client import TreasuryLLM
from modules.llm.prompts import build_system_prompt
from modules.llm.memory import init_memory, add_message, get_messages, clear_memory
from modules.llm.data_context import build_data_context

# Пайплайн отрисовки графиков
from modules.charts.chart_renderer import handle_chart_response

# Модули изменения данных
from modules.data_modification import (
    parse_modification_response,
    validate_operation,
    set_pending_operation,
    get_pending_operation,
    confirm_pending_operation,
    cancel_pending_operation
)
import re

# Свои стили для интерфейса чата
st.markdown("""
<style>
    .chat-header {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .assistant-info {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

ensure_session_data()

# Основной контент
st.markdown('<p class="chat-header">AI Treasury & Liquidity Assistant</p>', unsafe_allow_html=True)

# Инициализация памяти чата
init_memory()

# Клиент LLM
@st.cache_resource
def get_llm_client():
    return TreasuryLLM()

llm = get_llm_client()

# Системный промпт с актуальными данными из session_state
data_context = build_data_context()
system_prompt = build_system_prompt(data_context)

# Предупреждение если нет API-ключа
if not llm.groq_client:
    st.warning("GROQ_API_KEY is not set. Please check your .env file")

# История чата
for message in get_messages():
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ожидающие операции изменения данных
pending_op = get_pending_operation()
if pending_op:
    st.warning("⚠️ **Pending Data Modification requires your confirmation**")
    with st.expander("Operation Preview & Details", expanded=True):
        st.write(f"**Target Dataset:** `{pending_op.get('target_dataframe')}`")
        st.write(f"**Operation:** `{pending_op.get('operation')}`")
        if pending_op.get("target_record"):
            st.write(f"**Target Record:** `{pending_op.get('target_record')}`")
        st.write(f"**Changes:** `{pending_op.get('changes')}`")
        st.write(f"**Reasoning:** {pending_op.get('reasoning')}")
        st.write(f"**Risk Level:** {pending_op.get('risk_level', 'unknown').upper()}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm Operation", use_container_width=True, type="primary"):
                if confirm_pending_operation():
                    st.success("Operation executed successfully.")
                    add_message("assistant", f"✅ Successfully executed operation: {pending_op.get('operation')} on `{pending_op.get('target_dataframe')}`.")
                else:
                    st.error("Failed to execute operation.")
                st.rerun()
        with col2:
            if st.button("Cancel", use_container_width=True):
                cancel_pending_operation()
                st.info("Operation cancelled.")
                add_message("assistant", "Operation was cancelled by the user.")
                st.rerun()

# Ввод чата 
if not pending_op:
    if prompt := st.chat_input("Ask for treasury advice, request a chart, or update data..."):
        # Сообщение пользователя
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Сохраняем в память
        add_message("user", prompt)
        
        # Ответ ассистента
        with st.chat_message("assistant"):
            with st.spinner("Analyzing financial data..."):
                messages = get_messages()
                # Все сообщения диалога + контекст данных
                raw_response = llm.get_response(system_prompt, messages)
                
                if raw_response.startswith("Error"):
                    st.error(raw_response)
                else:
                    # Запрос на изменение данных
                    mod_op = parse_modification_response(raw_response)
                    
                    if mod_op:
                        # Проверка операции
                        val_res = validate_operation(mod_op)
                        
                        # Текстовая часть без JSON
                        text_response = re.sub(r'```json.*?```', '', raw_response, flags=re.DOTALL).strip()
                        if not text_response:
                            text_response = mod_op.get("reasoning", "I have prepared a data modification for your review.")
                            
                        if val_res["valid"]:
                            set_pending_operation(mod_op)
                            st.markdown(text_response)
                            add_message("assistant", text_response)
                            st.rerun()
                        else:
                            error_msg = f"I tried to perform an operation, but it was invalid: {val_res['error']}"
                            st.error(error_msg)
                            add_message("assistant", text_response + "\n\n" + error_msg)
                    else:
                        # Пайплайн графика: парсинг → проверка → построение → отрисовка
                        result = handle_chart_response(raw_response)
                        
                        if result["error"]:
                            if result["text"]:
                                st.markdown(result["text"])
                            st.warning(result["error"])
                            add_message("assistant", result["text"] if result["text"] else raw_response)
                        elif not result["has_chart"]:
                            # Обычный текстовый ответ
                            st.markdown(result["text"])
                            add_message("assistant", result["text"])
                        else:
                            # График уже отрисован пайплайном
                            memory_text = result["text"] if result["text"] else f"[Generated chart: {prompt}]"
                            add_message("assistant", memory_text)

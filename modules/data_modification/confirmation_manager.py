import streamlit as st
from .operation_executor import execute_operation

# Сохраняет операцию для подтверждения пользователем
def set_pending_operation(op: dict):
    st.session_state.pending_operation = op

# Возвращает ожидающую операцию
def get_pending_operation():
    return st.session_state.get("pending_operation")

# Очищает ожидающую операцию
def clear_pending_operation():
    if "pending_operation" in st.session_state:
        del st.session_state.pending_operation

# Выполняет ожидающую операцию и очищает её
def confirm_pending_operation() -> bool:
    op = get_pending_operation()
    if not op:
        return False
        
    success = execute_operation(op)
    clear_pending_operation()
    return success

# Отменяет ожидающую операцию
def cancel_pending_operation():
    clear_pending_operation()

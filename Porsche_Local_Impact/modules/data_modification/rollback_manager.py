import streamlit as st
import pandas as pd
from .operation_logger import log_operation
import os

# Сохраняет предыдущее состояние датафрейма для отката
def save_rollback_state(df_name: str, previous_df: pd.DataFrame, operation_desc: dict):
    if "rollback_history" not in st.session_state:
        st.session_state.rollback_history = []
        
    st.session_state.rollback_history.append({
        "df_name": df_name,
        "previous_df": previous_df,
        "operation_desc": operation_desc
    })

# Восстанавливает последнее состояние и пишет откат в лог
# Возвращает детали отката 
def perform_rollback() -> dict:
    if "rollback_history" not in st.session_state or not st.session_state.rollback_history:
        return {"success": False, "message": "No operations to rollback."}
        
    last_state = st.session_state.rollback_history.pop()
    df_name = last_state["df_name"]
    previous_df = last_state["previous_df"]
    operation_desc = last_state["operation_desc"]
    
    # Восстанавливаем датафрейм
    st.session_state[df_name] = previous_df
    
    # Сохраняем откат 
    persist_rollback_dataframe(df_name, previous_df)
    
    # Пишем лог
    log_operation({"type": "rollback", "rolled_back_op": operation_desc}, {}, {}, status="success_rollback")
    
    return {"success": True, "message": f"Successfully rolled back operation on {df_name}."}

#  датафрейм в CSV при откате
def persist_rollback_dataframe(df_name: str, df: pd.DataFrame):
    file_map = {
        "accounts_df": "data/accounts.csv",
        "scheduled_payments_df": "data/scheduled_payments.csv",
        "expected_inflows_df": "data/expected_inflows.csv"
    }
    
    file_path = file_map.get(df_name)
    if file_path and os.path.exists(os.path.dirname(file_path)):
        temp_path = file_path + ".tmp"
        df.to_csv(temp_path, index=False)
        os.replace(temp_path, file_path)

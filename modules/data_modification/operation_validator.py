import streamlit as st
import pandas as pd
from .operation_registry import ALLOWED_DATAFRAMES, ALLOWED_OPERATIONS

# Проверяет операцию изменения данных
# англ через ИИ
# Возвращает {"valid": bool, "error": str, "warning": str}
def validate_operation(op: dict) -> dict:
    if not isinstance(op, dict):
        return {"valid": False, "error": "Operation is not a valid dictionary.", "warning": None}
        
    action_type = op.get("action_type")
    if action_type != "data_modification":
        return {"valid": False, "error": "Not a data_modification operation.", "warning": None}
        
    df_name = op.get("target_dataframe")
    if df_name not in ALLOWED_DATAFRAMES:
        return {"valid": False, "error": f"Dataframe {df_name} is not allowed for modification.", "warning": None}
        
    if df_name not in st.session_state:
        return {"valid": False, "error": f"Dataframe {df_name} is not currently loaded.", "warning": None}
        
    operation = op.get("operation")
    if operation not in ALLOWED_OPERATIONS[df_name]:
        return {"valid": False, "error": f"Operation '{operation}' is not allowed on {df_name}.", "warning": None}
        
    # Проверяем 
    if operation == "update":
        target_record = op.get("target_record")
        if not target_record or not isinstance(target_record, dict):
            return {"valid": False, "error": "Missing or invalid 'target_record' for update operation.", "warning": None}
            
        # Убеждаемся что запись существует
        df = st.session_state[df_name]
        key_col = list(target_record.keys())[0]
        key_val = target_record[key_col]
        
        if key_col not in df.columns:
            return {"valid": False, "error": f"Identifier column '{key_col}' not found in {df_name}.", "warning": None}
            
        if not (df[key_col] == key_val).any():
            return {"valid": False, "error": f"Record with {key_col}='{key_val}' not found in {df_name}.", "warning": None}
            
    # Проверяем изменения
    changes = op.get("changes")
    if not changes or not isinstance(changes, dict):
        return {"valid": False, "error": "Missing or invalid 'changes'.", "warning": None}
        
    df = st.session_state[df_name]
    for col, val in changes.items():
        if operation == "update" and col not in df.columns:
            return {"valid": False, "error": f"Column '{col}' not found in {df_name}.", "warning": None}
            
        # Бизнес
        if isinstance(val, (int, float)) and val < 0 and "balance" in col:
            return {"valid": False, "error": f"Negative balance not allowed for '{col}'.", "warning": None}
            
    return {"valid": True, "error": None, "warning": None}

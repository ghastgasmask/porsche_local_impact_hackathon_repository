import streamlit as st
import pandas as pd
import os
from .operation_logger import log_operation
from .rollback_manager import save_rollback_state

# Выполняет проверенную операцию изменения данных
# Возвращает True при успехе, False при ошибке
def execute_operation(op: dict) -> bool:
    try:
        df_name = op["target_dataframe"]
        operation = op["operation"]
        changes = op["changes"]
        
        df = st.session_state[df_name]
        
        # Сохраняем состояние для отката
        save_rollback_state(df_name, df.copy(), op)
        
        old_values = {}
        affected_rows = 0
        
        if operation == "update":
            target_record = op["target_record"]
            key_col = list(target_record.keys())[0]
            key_val = target_record[key_col]
            
            #  индекс 
            idx = df[df[key_col] == key_val].index
            if len(idx) == 0:
                return False
                
            idx = idx[0]
            
            # Запоминаем старые 
            for col in changes.keys():
                old_values[col] = df.at[idx, col]
                
            # Применяем изменения
            for col, val in changes.items():
                df.at[idx, col] = val
                
            affected_rows = 1
            
        elif operation == "add":
            # Добавляем новую строку
            new_row = changes.copy()
            # target_record как запасной вариант для add 
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            st.session_state[df_name] = df
            affected_rows = 1
            
        # Пишем операцию в лог
        log_operation(op, old_values, changes, status="success")
        
        # Сохраняем в CSV
        persist_dataframe(df_name, df)
        
        return True
        
    except Exception as e:
        log_operation(op, {}, {}, status=f"failed: {str(e)}")
        return False

# охраняет датафрейм в CSV
def persist_dataframe(df_name: str, df: pd.DataFrame):
    # Датасеты лежат в папке data/
    file_map = {
        "accounts_df": "data/accounts.csv",
        "scheduled_payments_df": "data/scheduled_payments.csv",
        "expected_inflows_df": "data/expected_inflows.csv"
    }
    
    file_path = file_map.get(df_name)
    if file_path and os.path.exists(os.path.dirname(file_path)):
        # Сначала пишем во временный файл
        temp_path = file_path + ".tmp"
        df.to_csv(temp_path, index=False)
        # Потом заменяем оригинал
        os.replace(temp_path, file_path)

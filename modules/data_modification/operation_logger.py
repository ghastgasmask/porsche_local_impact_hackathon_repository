import json
import os
import datetime

LOG_FILE = "logs/operation_logs.jsonl"

# Записывает операцию в файл
def log_operation(op: dict, old_values: dict, new_values: dict, status: str):
    # Создаём папку для логов
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "operation_details": op,
        "old_values": old_values,
        "new_values": new_values,
        "status": status
    }
    
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

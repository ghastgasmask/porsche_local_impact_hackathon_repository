import json
import re

# Разбирает ответ ЛЛМ и достаёт JSON с инструкциями для изменения данных
def parse_modification_response(response_text: str) -> dict:
    # Ищем JSON  с data_modification
    json_match = re.search(r'```json\s*(\{.*"action_type"\s*:\s*"data_modification".*?\})\s*```', response_text, re.DOTALL | re.IGNORECASE)
    
    if json_match:
        json_str = json_match.group(1)
        try:
            parsed = json.loads(json_str)
            return parsed
        except json.JSONDecodeError:
            pass
            
    # любой JSON-блок если action_type не зашит в regex
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL | re.IGNORECASE)
    if json_match:
        json_str = json_match.group(1)
        try:
            parsed = json.loads(json_str)
            if parsed.get("action_type") == "data_modification":
                return parsed
        except json.JSONDecodeError:
            pass
            
    return None

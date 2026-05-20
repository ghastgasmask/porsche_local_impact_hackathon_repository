
# Chart Валидатор
# Строго проверяет инструкцию графика от ллМки на основе реестра
# Откланяет все что не поддерживается или опасно

from .chart_registry import DATASET_REGISTRY, ALLOWED_CHART_TYPES, ALLOWED_AGGREGATIONS


def validate_chart_instruction(instruction: dict) -> dict:
    # Проверяет инструкцию графика на основе реестра.
    # Возврат:
    # {"valid": True} 
    # {"valid": False, "error": "..."} 

    #  Что обязательно должно быть 
    required_keys = ["chart_type", "dataframe", "title"]
    for key in required_keys:
        if key not in instruction:
            return {"valid": False, "error": f"Missing required field: '{key}'"}

    # График
    chart_type = instruction["chart_type"]
    if chart_type not in ALLOWED_CHART_TYPES:
        return {
            "valid": False,
            "error": f"Unsupported chart type: '{chart_type}'. Allowed: {ALLOWED_CHART_TYPES}"
        }

    # Датафрейм
    df_name = instruction["dataframe"]
    if df_name not in DATASET_REGISTRY:
        return {
            "valid": False,
            "error": f"Unknown dataset: '{df_name}'. Available: {list(DATASET_REGISTRY.keys())}"
        }

    valid_columns = list(DATASET_REGISTRY[df_name]["columns"].keys())

    # Валидировать (x, y, values, names, color) 
    column_fields = ["x", "y", "values", "names", "color"]
    for field in column_fields:
        if field in instruction and instruction[field]:
            col = instruction[field]
            if col not in valid_columns:
                return {
                    "valid": False,
                    "error": f"Column '{col}' does not exist in '{df_name}'. Available columns: {valid_columns}"
                }

    # Агрегация
    agg = instruction.get("aggregation", "none")
    if agg not in ALLOWED_AGGREGATIONS:
        return {
            "valid": False,
            "error": f"Unsupported aggregation: '{agg}'. Allowed: {ALLOWED_AGGREGATIONS}"
        }

    #  Круговые графики требуют 'values' и 'names' 
    if chart_type == "pie":
        if "values" not in instruction or "names" not in instruction:
            return {
                "valid": False,
                "error": "Pie charts require both 'values' and 'names' fields."
            }

    #  Bar, line, scatter требуют 'x' и 'y' 
    if chart_type in ["bar", "line", "scatter"]:
        if "x" not in instruction or "y" not in instruction:
            return {
                "valid": False,
                "error": f"'{chart_type}' charts require both 'x' and 'y' fields."
            }

    # Если странные стринги, убрать вообще
    dangerous_keywords = ["import", "exec", "eval", "os.", "subprocess", "__", "open(", "lambda"]
    for key, value in instruction.items():
        if isinstance(value, str):
            for keyword in dangerous_keywords:
                if keyword in value.lower():
                    return {
                        "valid": False,
                        "error": f"Potentially dangerous content detected in field '{key}'."
                    }

    return {"valid": True}

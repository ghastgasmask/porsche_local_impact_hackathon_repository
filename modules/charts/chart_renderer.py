# Рендерим график
# Все от парса до дисплея

import streamlit as st

from .chart_parser import extract_chart_instruction, extract_text_response
from .chart_validator import validate_chart_instruction
from .chart_generator import generate_chart


def handle_chart_response(llm_response: str) -> dict:
   
    # Полный пайплайн: парсим, валидируем, создаем и рендерим

    # ответка от ЛЛМки:
    #     llm_response: текстовой ответ от ллм

    # Возврат:
    # библиотека с следующим:
    #         "has_chart": bool (сделали ли я график?)
    #         "text": str 
    #         "error": str 
    
    # Step 1: выевести объясненеие
    text_response = extract_text_response(llm_response)

    # Step 2: Пытаемся выевести график
    instruction = extract_chart_instruction(llm_response)
    if instruction is None:
        # Если не получилось
        return {"has_chart": False, "text": text_response, "error": None}

    # Step 3: Валидация
    validation = validate_chart_instruction(instruction)
    if not validation["valid"]:
        error_msg = f"⚠️ Chart validation failed: {validation['error']}"
        return {"has_chart": False, "text": text_response, "error": error_msg}

    # Step 4: Создать плотли
    fig = generate_chart(instruction)
    if fig is None:
        return {
            "has_chart": False,
            "text": text_response,
            "error": "⚠️ Could not generate chart......."
        }

    # Step 5: вначале показать текст, потом график
    if text_response:
        st.markdown(text_response)
    st.plotly_chart(fig, use_container_width=True)

    return {"has_chart": True, "text": text_response, "error": None}

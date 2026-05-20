# Suraganov's true master piece
# The Chart Parser
# Extracts structured JSON chart instructions from  LLM text
# Handles PROBLEMATICONS missing JSON, malformed output, extra text

import json
import re


def extract_chart_instruction(llm_response: str) -> dict | None:
    # SURAGANOV'S TRUE MASTER PIECE #2
    # Attempts to extract a JSON chart instruction from the LLM response
    # The LLM is instructed to return JSON inside ```json ... ``` blocks
    # This parser tries strategies to find it
    # Returns:
    # dict with chart instruction, or None if no chart instruction found
    
    
    
    
    # The Strategy 1: Look for ```json ... ``` code block
    json_block_pattern = r"```json\s*\n?(.*?)\n?\s*```"
    matches = re.findall(json_block_pattern, llm_response, re.DOTALL)
    for match in matches:
        parsed = _try_parse_json(match.strip())
        if parsed and _looks_like_chart(parsed):
            return parsed

    # Strategy 2: Look for ``` ... ``` blocks
    code_block_pattern = r"```\s*\n?(.*?)\n?\s*```"
    matches = re.findall(code_block_pattern, llm_response, re.DOTALL)
    for match in matches:
        parsed = _try_parse_json(match.strip())
        if parsed and _looks_like_chart(parsed):
            return parsed

    # Strategy 3: Look for { ... } anywhere in the response
    brace_pattern = r"\{[^{}]*\}"
    matches = re.findall(brace_pattern, llm_response, re.DOTALL)
    for match in matches:
        parsed = _try_parse_json(match.strip())
        if parsed and _looks_like_chart(parsed):
            return parsed

    # No chart instruction found
    return None


def extract_text_response(llm_response: str) -> str:
    # extract
    # Remove ```json ... ``` blocks
    cleaned = re.sub(r"```json\s*\n?.*?\n?\s*```", "", llm_response, flags=re.DOTALL)
    # Remove ``` ... ``` blocks
    cleaned = re.sub(r"```\s*\n?\{.*?\}\n?\s*```", "", cleaned, flags=re.DOTALL)
    # remove whitespace
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


def _try_parse_json(text: str) -> dict | None:
    # parse json
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def _looks_like_chart(data: dict) -> bool:
    # does my parsed dictionary look like a chart instruction?
    return isinstance(data, dict) and "chart_type" in data and "dataframe" in data

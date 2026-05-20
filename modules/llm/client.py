import os
from groq import Groq, APITimeoutError, APIError, AuthenticationError

from .config import get_api_key, get_model_name

class TreasuryLLM:
    def __init__(self):
        # клиент Groq ллм
        self.groq_client = None
        
        key = get_api_key()
        if key:
            self.groq_client = Groq(api_key=key, timeout=30.0)
                
    def get_response(self, system_prompt, messages):
        # Отправляет сообщение в LLM и ответ
        # Обрабатывает отсутствие ключа
        if not self.groq_client:
            return "Error: Groq API key is missing. Please check your environment variables."
        try:
            # все старый дебаг не чекать пж
            formatted_messages = [{"role": "system", "content": system_prompt}] + messages
            response = self.groq_client.chat.completions.create(
                model=get_model_name(),
                messages=formatted_messages,
                max_tokens=1500
            )
            content = response.choices[0].message.content
            if not content:
                return "Error: Received an empty response from the Groq API."
            return content
        except APITimeoutError:
            return "Error: The Groq API request timed out. Please try again later."
        except AuthenticationError:
            return "Error: Groq API key is invalid."
        except APIError as e:
            return f"Error: Groq API encountered an error: {str(e)}"
        except Exception as e:
            return f"Error: An unexpected error occurred: {str(e)}"

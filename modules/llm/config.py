import os
from dotenv import load_dotenv

load_dotenv()

def get_api_key():
    return os.getenv("GROQ_API_KEY")

def get_model_name():
    return "llama-3.3-70b-versatile"

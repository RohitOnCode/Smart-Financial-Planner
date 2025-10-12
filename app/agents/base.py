
from langchain_openai import ChatOpenAI
from app.config import OPENAI_API_KEY, MODEL_NAME
def get_llm(**kwargs):
    return ChatOpenAI(api_key=OPENAI_API_KEY, model=MODEL_NAME, temperature=kwargs.get('temperature', 0.2))

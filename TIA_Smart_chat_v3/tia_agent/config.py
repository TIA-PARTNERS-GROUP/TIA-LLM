from google.adk.models.lite_llm import LiteLlm
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Use OpenAI model with LiteLLM
CHAT_MODEL = "openai/gpt-4o-mini"
AGENT_MODEL = LiteLlm(model=f"openai/gpt-4o-mini")

# RapidAPI configuration
RAPIDAPI_HOST = "local-business-data.p.rapidapi.com"
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
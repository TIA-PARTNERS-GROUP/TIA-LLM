from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
import os

os.environ["OPENAI_API_KEY"] = "unused"
os.environ["OPENAI_API_BASE"] = "http://localhost:11434/v1"

#OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_MODEL = "qwen3:14b"
#OLLAMA_MODEL = "qwen3:8b"
MAX_STEP = 31
model = LiteLlm(model=f"openai/{OLLAMA_MODEL}")
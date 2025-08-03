from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
import os
from typing import Optional

# Model Configuration Options
MODEL_TYPE = os.getenv("MODEL_TYPE", "local")  # "local" or "api"

# Local Ollama Configuration
OLLAMA_MODELS = {
    "qwen2.5:7b": "qwen2.5:7b",
    "qwen3:14b": "qwen3:14b", 
    "qwen3:8b": "qwen3:8b"
}
DEFAULT_OLLAMA_MODEL = "qwen3:14b"

# API Model Configuration  
API_MODELS = {
    "gemini": "gemini-1.5-flash",
    "gemini-pro": "gemini-1.5-pro", 
    "gpt-4": "gpt-4-turbo-preview",
    "gpt-3.5": "gpt-3.5-turbo"
}
DEFAULT_API_MODEL = "gemini"

def get_model(model_type: Optional[str] = None, model_name: Optional[str] = None):
    """
    Get the appropriate model based on configuration.
    
    Args:
        model_type: "local" for Ollama or "api" for cloud models
        model_name: Specific model to use
    """
    model_type = model_type or MODEL_TYPE
    
    if model_type == "local":
        # Configure for local Ollama
        os.environ["OPENAI_API_KEY"] = "unused"
        os.environ["OPENAI_API_BASE"] = "http://localhost:11434/v1"
        
        selected_model = model_name or DEFAULT_OLLAMA_MODEL
        if selected_model not in OLLAMA_MODELS:
            selected_model = DEFAULT_OLLAMA_MODEL
            
        return LiteLlm(model=f"openai/{OLLAMA_MODELS[selected_model]}")
    
    elif model_type == "api":
        selected_model = model_name or DEFAULT_API_MODEL
        
        if selected_model.startswith("gemini"):
            # Use Gemini model via LiteLLM
            return LiteLlm(model=f"gemini/{API_MODELS.get(selected_model, API_MODELS['gemini'])}")
        elif selected_model.startswith("gpt"):
            # Use OpenAI models via LiteLLM
            return LiteLlm(model=API_MODELS.get(selected_model, API_MODELS["gpt-4"]))
        else:
            # Default to Gemini via LiteLLM
            return LiteLlm(model=f"gemini/{API_MODELS['gemini']}")
    
    else:
        raise ValueError(f"Invalid model_type: {model_type}. Must be 'local' or 'api'")

# Default model instance
model = get_model()

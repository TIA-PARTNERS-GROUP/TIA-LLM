"""
Utility functions for TIA Smart Chat v2
"""

import os
from typing import Dict, Any, Optional
from .config import get_model, MODEL_TYPE, OLLAMA_MODELS, API_MODELS
from .agent import create_agent_with_model, root_agent


def switch_model(model_type: str, model_name: Optional[str] = None) -> Any:
    """
    Switch the global model configuration.
    
    Args:
        model_type: "local" or "api"
        model_name: Specific model to use
        
    Returns:
        New model instance
    """
    os.environ["MODEL_TYPE"] = model_type
    return get_model(model_type, model_name)


def get_available_models() -> Dict[str, Any]:
    """Get list of available models for both local and API."""
    return {
        "local": list(OLLAMA_MODELS.keys()),
        "api": list(API_MODELS.keys())
    }


def create_conversation_session(model_type: str = "local", model_name: Optional[str] = None):
    """
    Create a new conversation session with specified model.
    
    Args:
        model_type: "local" or "api"
        model_name: Specific model to use
        
    Returns:
        Configured agent ready for conversation
    """
    if model_type == MODEL_TYPE and model_name is None:
        # Use default agent
        return root_agent
    else:
        # Create agent with custom model
        return create_agent_with_model(model_type, model_name)


def get_model_info() -> Dict[str, Any]:
    """Get information about current model configuration."""
    return {
        "current_type": MODEL_TYPE,
        "available_models": get_available_models(),
        "local_endpoint": "http://localhost:11434/v1" if MODEL_TYPE == "local" else None
    }


class ConversationManager:
    """
    Manager class for handling multiple conversation sessions.
    """
    
    def __init__(self):
        self.sessions = {}
        self.active_session = None
    
    def create_session(self, session_id: str, model_type: str = "local", model_name: Optional[str] = None):
        """Create a new conversation session."""
        agent = create_conversation_session(model_type, model_name)
        self.sessions[session_id] = {
            "agent": agent,
            "model_type": model_type,
            "model_name": model_name,
            "state": {}
        }
        self.active_session = session_id
        return agent
    
    def get_session(self, session_id: str):
        """Get an existing session."""
        return self.sessions.get(session_id)
    
    def switch_session(self, session_id: str):
        """Switch to a different session."""
        if session_id in self.sessions:
            self.active_session = session_id
            return self.sessions[session_id]["agent"]
        return None
    
    def list_sessions(self):
        """List all active sessions."""
        return {
            session_id: {
                "model_type": session["model_type"],
                "model_name": session["model_name"]
            }
            for session_id, session in self.sessions.items()
        }
    
    def delete_session(self, session_id: str):
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            if self.active_session == session_id:
                self.active_session = None
            return True
        return False

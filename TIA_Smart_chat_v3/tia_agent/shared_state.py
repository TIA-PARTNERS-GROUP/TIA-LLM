"""Shared state across the application"""
from typing import Dict, Any
from .sub_agents.DynamicChatAssistant import DynamicChatAssistant
from .sub_agents.vision_agent.prompts import VISION_RULE_PROMPT, TIA_VISION_CHAT_1_FOUNDATION_PROMPT, TIA_VISION_CHAT_2_REFLECTION_PROMPT, TIA_VISION_CHAT_3_ANALYSIS_PROMPT, TIA_VISION_CHAT_4_STRATEGY_PROMPT
import logging

logger = logging.getLogger(__name__)

VISION_PROMPTS = [
    TIA_VISION_CHAT_1_FOUNDATION_PROMPT,
    TIA_VISION_CHAT_2_REFLECTION_PROMPT,
    TIA_VISION_CHAT_3_ANALYSIS_PROMPT,
    TIA_VISION_CHAT_4_STRATEGY_PROMPT
]

"""
Global session storage.
Handles the user session for DynamicChatAssistant instances.
Key: session_id, Value: DynamicChatAssistant instance.
"""

# NOTE: FUTURE IMPROVEMENT - Consider using a Database or a proper Cache system. May require DynamicChatAssistant to be serialized or a slight redesign.
user_sessions: Dict[str, DynamicChatAssistant] = {}

def get_or_create_assistant(session_id: str, user_id: int, chat_type: str) -> DynamicChatAssistant:
    """Get or create an assistant instance for a specific session."""
    try:
        logger.debug(f"Getting or creating assistant for session_id: {session_id}, user_id: {user_id}, chat_type: {chat_type}")
        if session_id not in user_sessions:
            if chat_type == "profiler:VisionAgent":
                assistant = DynamicChatAssistant(VISION_PROMPTS, VISION_RULE_PROMPT, user_id)
            assistant.session_id = session_id
            user_sessions[session_id] = assistant

        return user_sessions[session_id]
    except Exception as e:
        logger.debug(f"ERROR in get_or_create_assistant: {e}")
        raise Exception("Error creating or retrieving assistant: " + str(e))

def cleanup_session(session_id: str):
    """Clean up a session"""
    if session_id in user_sessions:
        del user_sessions[session_id]
    logger.debug(f"Cleaned up session {session_id}")
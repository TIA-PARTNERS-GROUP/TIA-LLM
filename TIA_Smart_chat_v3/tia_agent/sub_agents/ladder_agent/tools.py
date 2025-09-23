from google.adk.tools.tool_context import ToolContext
from ..DynamicChatAssistant import DynamicChatAssistant
from typing import Dict, Any
from .prompts import DYNAMIC_CHAT_RULE_PROMPT, TIA_LADDER_CHAT_1_VISION_PROMPT, TIA_LADDER_CHAT_2_MASTERY_PROMPT, TIA_LADDER_CHAT_3_TEAM_PROMPT, TIA_LADDER_CHAT_4_VALUE_PROMPT, TIA_LADDER_CHAT_5_BRAND_PROMPT
import uuid

CHAT_PROMPTS = [
    TIA_LADDER_CHAT_1_VISION_PROMPT,
    TIA_LADDER_CHAT_2_MASTERY_PROMPT,
    TIA_LADDER_CHAT_3_TEAM_PROMPT,
    TIA_LADDER_CHAT_4_VALUE_PROMPT,
    TIA_LADDER_CHAT_5_BRAND_PROMPT
]

_user_sessions = {}

def get_or_create_assistant(session_id: str, user_id: int = None):
    """Get or create an assistant instance for a specific session."""
    global _user_sessions

    if not session_id:
        session_id = str(uuid.uuid4())

    # If the session doesn't exist, create a new assistant
    if session_id not in _user_sessions:
        assistant = DynamicChatAssistant(CHAT_PROMPTS, DYNAMIC_CHAT_RULE_PROMPT, user_id)
        assistant.session_id = session_id
        _user_sessions[session_id] = assistant

    return _user_sessions[session_id]

def start_new_conversation(tool_context: ToolContext) -> Dict[str, Any]:
    """Start anew chat but if existing session, continue it"""
    try:
        state = tool_context.state
        user_id = state.get("user_id", "UNKNOWN_USER")
        print(f"USER ID: {user_id}")
        if "LadderAgent" not in state:
            state["LadderAgent"] = {}
        ladder_state = state["LadderAgent"]
        session_id = ladder_state.get("session_id", None)

        assistant = get_or_create_assistant(session_id, user_id)
        print(f"DEBUG: Chat session with ID: {assistant.session_id}")
        session_id = ladder_state["session_id"] = assistant.session_id

        chat_state = ladder_state["chat_state"] = "chat"
        current_phase = ladder_state["current_phase"] = assistant.current_phase
        total_phases = ladder_state["total_phases"] = len(assistant.prompts) - 1

        response = assistant.send_message("Help me scale my business")

        return {"status": "success", 
                "session_id": session_id, 
                "chat_state": chat_state, 
                "response": response, 
                "phase": current_phase, 
                "total_phases": total_phases
                }
    except Exception as e:
        return {"status": "error", "message": str(e), "chat_state": "exit"}

def chat_with_phases(user_input: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Return message from the dynamic TIA assistant chat"""
    try:
        state = tool_context.state
        ladder_state = state["LadderAgent"]

        if ladder_state is None:
            raise ValueError("LadderAgent state is not initialized.")
        session_id = ladder_state.get("session_id", None)
        assistant = get_or_create_assistant(session_id)

        chat_state = ladder_state.get("chat_state")
        current_phase = ladder_state.get("current_phase")
        total_phases = ladder_state.get("total_phases")
        
        if user_input.lower() in ['quit', 'exit', 'bye', 'end session', 'reset']:
            chat_state = ladder_state["chat_state"] = "exit"
            assistant.save_responses()
            return {"status": "success", "chat_state": chat_state}
        
        response = assistant.send_message(user_input)

        current_phase = assistant.current_phase
        ladder_state["current_phase"] = current_phase

        state["LadderAgent"] = ladder_state
        if "<exit>" in response:
            chat_state = ladder_state["chat_state"] = "exit"
            state["user_profile"] = "collected"
            state["LadderAgent"] = ladder_state
            return {"status": "success", 
                    "chat_state": chat_state, 
                    "response": response
                    }

        return {"status": "success", 
                "session_id": session_id, 
                "chat_state": chat_state, 
                "response": response, 
                "current_phase": current_phase, 
                "total_phases": total_phases
                }
    
    except Exception as e:
        return {"status": "error", "message": str(e), "chat_state": "exit"}
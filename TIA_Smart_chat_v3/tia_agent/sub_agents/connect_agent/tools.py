from typing import Dict, Any
from google.adk.tools.tool_context import ToolContext
from ..DynamicChatAssistant import DynamicChatAssistant
from .utils import recommended_GNN_connection, recommended_WEB_connection, generate_email_templates, extract_business_type
from TIA_Smart_chat_v3.tia_agent.utils import validate_connection_options
from .prompts import (
    CONNECT_RULE_PROMPT,
    CONNECT_CHAT_1_BUSINESS_INFO_PROMPT
)
import uuid

CONNECT_PROMPTS = [
    CONNECT_CHAT_1_BUSINESS_INFO_PROMPT
]

_user_sessions = {}

def get_or_create_assistant(session_id: str, user_id: int = None):
    """Get or create an assistant instance for a specific session."""
    global _user_sessions

    if not session_id:
        session_id = str(uuid.uuid4())

    # If the session doesn't exist, create a new assistant
    if session_id not in _user_sessions:
        assistant = DynamicChatAssistant(CONNECT_PROMPTS, CONNECT_RULE_PROMPT, user_id)
        assistant.session_id = session_id
        _user_sessions[session_id] = assistant

    return _user_sessions[session_id]

def recommended_connection(tool_context: ToolContext):
    try:
        state = tool_context.state
        required_keys = ["user_id", "region", "lat", "lng", "Generated_Profile", "connection_type"]
        missing = [k for k in required_keys if state.get(k) is None]
        if missing:
            return {"status": "error", "message": f"Missing required attributes: {', '.join(missing)}"}
        
        attributes = {
            "name": state.get("name"),
            "user_id": state.get("user_id"),
            "region": state.get("region"),
            "lat": state.get("lat"),
            "lng": state.get("lng"),
            "profile": state.get("Generated_Profile"),
            "connection_type": state.get("connection_type"),  # Add this
        }
        
        # Optional: Validate profile before proceeding
        is_valid, msg = validate_connection_options(attributes["connection_type"], attributes["profile"])
        if not is_valid:
            return {"status": "error", "message": msg}
        
        GNN_CALL = recommended_GNN_connection(attributes)
        if GNN_CALL is not None:
            # Store the result in state
            if "ConnectAgent" not in state:
                state["ConnectAgent"] = {}
            state["ConnectAgent"]["connection_result"] = GNN_CALL
            return {"status": "success", "connection_result": GNN_CALL}

        WEB_CALL = recommended_WEB_connection(attributes)
        
        # Store the result in state
        if "ConnectAgent" not in state:
            state["ConnectAgent"] = {}
        state["ConnectAgent"]["connection_result"] = WEB_CALL
        
        return {"status": "success", "connection_result": WEB_CALL}
    
    except Exception as e:
        print(f"Error in recommended_connection: {e}")
        return {"status": "error", "message": str(e)}

def generate_email(tool_context: ToolContext):
    """
    Generate email templates for the recommended businesses.
    Pulls the connection_result from the state.
    """
    try:
        state = tool_context.state
        if "ConnectAgent" not in state or "connection_result" not in state["ConnectAgent"]:
            return {"status": "error", "message": "No connection_result found in state. Call recommended_connection first."}
        
        # Retrieve the stored result
        connection_result = state["ConnectAgent"]["connection_result"]
        businesses = connection_result.get("data", [])
        if not businesses:
            return {"status": "error", "message": "No business data found in connection_result."}
        
        # Get user details for email personalization
        generated_profile = state.get("Generated_Profile", {})
        user_name = generated_profile.get("UserName")
        user_job = generated_profile.get("UserJob")
        user_email = generated_profile.get("Contact_Email")
        business_name = generated_profile.get("Business_Name")
        # Generate email templates using the new function
        print(f"DEBUG: User details - Name: {user_name}, Job: {user_job}, Email: {user_email}, Business: {business_name}")
        print(f"DEBUG: Number of businesses to generate emails for: {len(businesses)}")
        print(f"DEBUG: Connection results: {connection_result}")
        print("DEBUG: Generating email templates...")
        email_templates = generate_email_templates(businesses, user_name, user_job, user_email, business_name)
        if not email_templates:
            return {"status": "error", "message": "Failed to generate email templates."}
        
        # tool_context.actions.transfer_to_agent = "CoordinatorAgent"
        state["set_agent"] = "CoordinatorAgent"
        return {"status": "success", "email_templates": email_templates}
    
    except Exception as e:
        return {"status": "error", "message": str(e), "chat_state": "exit"}

def start_new_conversation(tool_context: ToolContext):
    """Start a new SmartConnect session"""
    try:
        state = tool_context.state

        # Check for profile generation
        if state.get("user_profile") == "generated":
            print("DEBUG: Profile already generated, calling recommended_connection directly")
            connection_result = recommended_connection(tool_context)
            if connection_result.get("status") == "success":
                email_result = generate_email(tool_context)
                return email_result
            else:
                return connection_result

        user_id = state.get("user_id", "UNKNOWN_USER")
        if "ConnectAAgent" not in state:
            state["ConnectAgent"] = {}
        connect_state = state["ConnectAgent"]
        session_id = connect_state.get("session_id", None)
        print(f"DEBUG: start_session_phases called with session_id={session_id}")

        assistant = get_or_create_assistant(session_id, user_id)
        print(f"DEBUG: Chat session with ID: {assistant.session_id}")
        session_id = connect_state["session_id"] = assistant.session_id

        chat_state = connect_state["chat_state"] = "chat"
        current_phase = connect_state["current_phase"] = assistant.current_phase
        total_phases = connect_state["total_phases"] = len(assistant.prompts) - 1

        response = assistant.send_message("Lets Begin!")

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
    """Chat with the SmartConnect assistant"""
    try:
        state = tool_context.state
        connect_state = state["ConnectAgent"]

        if connect_state is None:
            raise ValueError("VisionAgent state is not initialized.")
        session_id = connect_state.get("session_id", None)
        assistant = get_or_create_assistant(session_id)

        chat_state = connect_state["chat_state"] = "chat"
        current_phase = connect_state.get("current_phase")
        total_phases = connect_state.get("total_phases")
        
        if user_input.lower() in ['quit', 'exit', 'bye', 'end session', 'reset']:
            chat_state = connect_state["chat_state"] = "exit"
            assistant.save_responses()
            return {"status": "success", "chat_state": chat_state}
        
        response = assistant.send_message(user_input)

        current_phase = assistant.current_phase
        connect_state["current_phase"] = current_phase

        state["ConnectAgent"] = connect_state
        if "<exit>" in response:
            chat_state = connect_state["chat_state"] = "exit"
            state["user_profile"] = "generated"
            state["ConnectAgent"] = connect_state

            # Initialize Generated_Profile if not present
            if "Generated_Profile" not in state:
                state["Generated_Profile"] = {}
            
            # Extract conversation history for analysis
            conversation_history = assistant.collect_user_history()  # Assuming this method exists in DynamicChatAssistant
            
            # Extract business_type using the new function
            business_type = extract_business_type(conversation_history)
            state["Generated_Profile"]["business_type"] = business_type

            return {"status": "success", 
                    "chat_state": chat_state, 
                    "response": response
                    }

        return {"status": "success", 
                "session_id": session_id,
                "chat_state": chat_state, 
                "response": response, 
                "phase": current_phase, 
                "total_phases": total_phases
                }
    
    except Exception as e:
        return {"status": "error", "message": str(e), "chat_state": "exit"}
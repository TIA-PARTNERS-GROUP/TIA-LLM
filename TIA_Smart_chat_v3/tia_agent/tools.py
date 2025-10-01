from google.adk.tools import ToolContext
from .utils import load_user_profile, validate_connection_options

def end_session(tool_context: ToolContext) -> dict:
    """End the current session."""
    try:
        state = tool_context.state
        user_profile = state.get("user_profile", "not_generated")
        if user_profile == "collected":
            state["set_agent"] = "ProfilerAgent"
            return {"status": "success", "transfer_to_agent": "ProfilerAgent"}
        else:
            state["end_session"] = True
            return {"status": "success", "session": "ending"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def check_for_existing_user(tool_context: ToolContext):
    """Check the database for existing user profile and pull data if available."""
    try:
        state = tool_context.state
        user_id = state.get("user_id")
        if not user_id:
            return {"status": "error", "message": "User ID not found in state."}
        
        # Load user profile from the database
        result = load_user_profile(user_id)
        print(f"DEBUG: load_user_profile result: {result}")
        if result.get("profile_exists"):
            state["Generated_Profile"] = result["profile"]
            state["user_profile"] = "generated"
        else:
            state["Generated_Profile"] = result["profile"]
            state["user_profile"] = "not_generated"

        # Check for valid connection options
        connection_type = state.get("connection_type")
        if connection_type and result.get("profile_exists"):
            is_valid, message = validate_connection_options(connection_type, result["profile"])
            if not is_valid:
                return {"status": "error", "message": message}
            result = {"status": "success", "profile": result["profile"], "message": f"User profile loaded and valid for {connection_type} connection."}

        agent_type = state.get("set_agent")
        return {"status": "success", "transfer_to_agent": agent_type, "result": result}

    except Exception as e:
        print(f"DEBUG: Error in check_for_existing_user: {e}")
        return {"status": "error", "message": str(e)}
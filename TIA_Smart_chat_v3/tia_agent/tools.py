from google.adk.tools import ToolContext
from .utils import load_user_profile, validate_connection_options

def check_for_existing_user(tool_context: ToolContext):
    """Check the database for existing user profile and pull data if available."""
    try:
        state = tool_context.state
        user_id = state.get("user_id")
        if not user_id:
            return {"status": "error", "message": "User ID not found in state."}
        
        # Load user profile from the database
        result = load_user_profile(user_id)
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

        return result

    except Exception as e:
        print(f"DEBUG: Error in check_for_existing_user: {e}")
        return {"status": "error", "message": str(e)}
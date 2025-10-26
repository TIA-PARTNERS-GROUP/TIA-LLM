from google.adk.tools import ToolContext
from .utils import load_user_profile, validate_connection_options
import logging

logger = logging.getLogger(__name__)

def end_session(tool_context: ToolContext) -> dict:
    """End the current session."""
    try:
        logger.debug("Ending session")
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
        logger.debug("Starting check_for_existing_user")
        state = tool_context.state
        user_id = state.get("user_id")
        if not user_id:
            return {"status": "error", "message": "User ID not found in state."}
        
        # Load user profile from the database
        result = load_user_profile(user_id)
        logger.debug(f"load_user_profile result: {result}")
        if result.get("profile_exists"):
            state["Generated_Profile"] = result["profile"]
            state["user_profile"] = "generated"
        else:
            state["Generated_Profile"] = result["profile"]
            state["user_profile"] = "not_generated"

        agent_type = state.get("set_agent")
        return {"status": "success", "transfer_to_agent": agent_type, "result": result}

    except Exception as e:
        logger.error(f"Error in check_for_existing_user: {e}")
        return {"status": "error", "message": str(e)}
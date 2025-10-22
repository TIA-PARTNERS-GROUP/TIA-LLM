from google.adk.tools import ToolContext
from .utils import model_update_user_details
from ...shared_state import get_or_create_assistant, cleanup_session
import logging

logger = logging.getLogger(__name__)

# Search through the temp directory for the users most recent saved conversation history
def collect_user_history(tool_context: ToolContext):
    """Collect user history from VisionAgent session data"""
    try:
        logger.debug("Collecting user history")
        state = tool_context.state
        user_id = state.get("user_id")
        session_id = state.get("session_id")
        
        # Retrieve the DynamicChatAssistant instance's history
        if session_id:
            assistant = get_or_create_assistant(session_id, user_id, "profiler:VisionAgent")
            logger.debug("Found assistant: %s", assistant)
            if assistant and assistant.user_responses:
                logger.debug("Found user history: %s", assistant.user_responses)
                cleanup_session(session_id)  # Clean up after retrieving history
                return {"status": "success", "user_history": assistant.user_responses}
        
        return {"status": "error", "message": "No conversation history found in session."}
    except Exception as e:
        logger.error(f"Error in collect_user_history: {e}")
        return {"status": "error", "message": str(e)}

def store_user_profile(tool_context: ToolContext):
    """Store the generated user profile"""
    try:
        state = tool_context.state
        user_id = state.get("user_id")
        profile = state.get("Generated_Profile", {})
        logger.debug("Storing user profile for user_id: %s", user_id)

        user_role = profile.get("UserJob")
        user_strengths = [s.strip() for s in profile.get("User_Strength", "").split(",") if s.strip()]
        user_skills = [s.strip() for s in profile.get("User_skills", "").split(",") if s.strip()]
        business_strengths = [s.strip() for s in profile.get("Business_Strength", "").split(",") if s.strip()]
        business_type = profile.get("Business_Type")
        business_category = profile.get("Business_Category")
        skill_category = profile.get("Skill_Category")
        strength_category = profile.get("Strength_Category")


        logger.debug("RUNNING model_update_user_details")
        if not model_update_user_details(
            user_id,
            user_role,
            user_strengths,
            user_skills,
            business_strengths,
            business_type,
            business_category,
            skill_category,
            strength_category
        ):
            raise Exception("Failed to update user profile in database.")

        state["end_session"] = True
        return {"status": "success", "profile": profile}
    except Exception as e:
        logger.error(f"Error in store_user_profile: {e}")
        return {"status": "error", "message": str(e)}

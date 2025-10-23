from google.adk.tools.tool_context import ToolContext
from .utils import recommended_GNN_connection, recommended_WEB_connection, generate_email_templates, extract_business_type
import logging

logger = logging.getLogger(__name__)

def recommended_connection(tool_context: ToolContext):
    """
    Recommend connections based on user profile and location.
    """
    try:
        state = tool_context.state
        connect_agent_state = state.get("ConnectAgent", {})

        logger.debug(f"Tool_context.state type: {state}")
        logger.debug(f"Tool_context.state: {state}")
        logger.debug(f"connection_type value: '{state.get('connection_type')}'")
        logger.debug(f"connection_type in state: {'connection_type' in state}")

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
            "connection_type": state.get("connection_type"),
            "ConnectAgent": state.get("ConnectAgent", {})
        }
        
        # Store the result in state
        if "ConnectAgent" not in state:
            state["ConnectAgent"] = {}

        GNN_CALL = recommended_GNN_connection(attributes)
        if GNN_CALL is not None:
            result_type = "Existing TIA Users"
            result = GNN_CALL

            # Extract user IDs
            user_ids = [rec["recommendation"]["user"]["id"] for rec in GNN_CALL]
            connect_agent_state["existing_users"] = user_ids
        else:
            WEB_CALL = recommended_WEB_connection(attributes)
            if WEB_CALL is not None:
                result_type = "Web Search"
                result = WEB_CALL

        if result is None:
            return {"status": "error", "message": "No connections found from web search."}

        connect_agent_state["connection_type"] = result_type
        connect_agent_state["connection_result"] = result
        state["ConnectAgent"] = connect_agent_state
        
        return {"status": "success", "connection_type": result_type, "connection_result": result}
    
    except Exception as e:
        logger.error(f"Error in recommended_connection: {e}")
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
        connection_type = state["ConnectAgent"].get("connection_type")

        if connection_type == "Existing TIA Users":
            businesses = connection_result
        elif connection_type == "Web Search":
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
        logger.debug(f"User details - Name: {user_name}, Job: {user_job}, Email: {user_email}, Business: {business_name}")
        logger.debug(f"Number of businesses to generate emails for: {len(businesses)}")
        logger.debug(f"Connection results: {connection_result}")
        logger.debug("Generating email templates...")
        email_templates = generate_email_templates(businesses, user_name, user_job, user_email, business_name)
        if not email_templates:
            return {"status": "error", "message": "Failed to generate email templates."}
        
        return {"status": "success", "email_templates": email_templates}
    
    except Exception as e:
        logger.error(f"Error in generate_email: {e}")
        return {"status": "error", "message": str(e), "chat_state": "exit"}

def store_connect_chat(tool_context: ToolContext):
    """Store the generated connection chat state"""
    try:
        logger.debug("Storing ConnectAgent chat state")
        state = tool_context.state
        connect_agent_state = state.get("ConnectAgent", {})
        
        # Extract business type from the profile
        profile = state.get("Generated_Profile", {})
        business_type = extract_business_type(profile)
        connect_agent_state["business_type"] = business_type
        state["ConnectAgent"] = connect_agent_state
        
        return {"status": "success", "ConnectAgent": connect_agent_state}
    except Exception as e:
        logger.error(f"Error in store_connect_chat: {e}")
        return {"status": "error", "message": str(e)}
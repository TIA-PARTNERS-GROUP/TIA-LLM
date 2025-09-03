from google.adk.tools import ToolContext

# IMPLEMENT WITH GNN AND DATABASE
def check_for_existing_user(tool_context: ToolContext):
    "Check the database to see if there is an existing user."
    try:
        state = tool_context.state

        # Check for generated profile in state
        user_profile = state.get("user_profile")
        profile_exists = False
        if user_profile:
            # Assuming user_profile is a dict or string; parse for essentials
            if isinstance(user_profile, dict):
                user = user_profile.get("User")
                idea = user_profile.get("Idea")
                user_post = user_profile.get("UserPost")
            else:
                user = idea = user_post = None

            # Check if all 3 essentials are present
            if user and idea and user_post:
                profile_exists = True

        # Update state based on check
        if profile_exists:
            state["user_profile"] = "generated"
            return {"status": "success", "profile_exists": True}
        else:
            state["user_profile"] = None
            return {"status": "success", "profile_exists": False}
    except Exception as e:
        return {"status": "error", "message": str(e)}
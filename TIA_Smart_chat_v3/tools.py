from google.adk.tools import ToolContext

# IMPLEMENT WITH GNN AND DATABASE
def check_for_existing_user(tool_context: ToolContext):
    "Check the database to see if there is an existing user."
    try:
        # Database query logic here
        state = tool_context.state

        # TEST: ADD GNN/SQL LOGIC LATER
        profile_exist = False
        sample_profile = {
            "User": "John Doe",
            "Idea": "Build an AI-powered chatbot",
            "UserPost": "Software Engineer",
            "Strength": "Problem-solving"
        }
        
        if profile_exist:
            state["user_state"] = "existing_user"
            state["user_profile"] = sample_profile
            return {"status": "success", "user_state": "existing_user"}
        else:
            state["user_state"] = "not_existing_user"
            state["user_profile"] = None
            return {"status": "success", "user_state": "not_existing_user"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
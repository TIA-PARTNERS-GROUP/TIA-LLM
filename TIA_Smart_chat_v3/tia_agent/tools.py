from google.adk.tools import ToolContext

# IMPLEMENT WITH GNN AND DATABASE
def check_for_existing_user(tool_context: ToolContext):
    "Check the database to see if there is an existing user."
    try:
        # Database query logic here
        state = tool_context.state


        # INSERT ADD TO SQL NODE OR GNN CODE HERE
        # TEST: ADD GNN/SQL LOGIC LATER
        profile_exist = False
        sample_profile = {
            "User": "John Doe",
            "Idea": "Build an AI-powered chatbot",
            "UserPost": "Software Engineer",
            "Strength": "Problem-solving"
        }


        # Sample user ID
        state["user_id"] = 1
        state["region"] = "au"
        state["lat"] = 0.0
        state["lng"] = 0.0

        if profile_exist:
            state["user_profile"] = sample_profile
            return {"status": "success", "user_profile": sample_profile}
        else:
            state["user_profile"] = None
            return {"status": "success", "user_profile": None}
    except Exception as e:
        return {"status": "error", "message": str(e)}
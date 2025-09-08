from google.adk.tools import ToolContext

# TODO: IMPLEMENT WITH GNN AND DATABASE
def check_for_existing_user(tool_context: ToolContext):
    "Check the database to see if there is an existing user."
    try:
        state = tool_context.state

        # Check for generated profile in state
        gen_profile = state.get("Generated_Profile")
        profile_exists = False
        if gen_profile:
            # Updated to match new schema fields
            if isinstance(gen_profile, dict):
                business_name = gen_profile.get("Business_Name")
                user_job = gen_profile.get("UserJob")
                user_strength = gen_profile.get("User_Strength")
            else:
                business_name = user_job = user_strength = None

            # Check if all 3 essentials are present
            if business_name and user_job and user_strength:
                profile_exists = True

        # Update state based on check
        if profile_exists:
            state["user_profile"] = "generated"
            return {"status": "success", "profile_exists": True}
        else:
            state["user_profile"] = "not_generated"
            return {"status": "success", "profile_exists": False}
    except Exception as e:
        return {"status": "error", "message": str(e)}
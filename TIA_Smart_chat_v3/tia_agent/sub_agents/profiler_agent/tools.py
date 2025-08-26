from google.adk.tools import ToolContext
from datetime import datetime
import os, json, re

# Search through the temp directory for the users most recent saved conversation history
def collect_user_history(tool_context: ToolContext):
    """Find the user's most recent conversation history from "__DATE-*.json" files under temp"""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Go up 3 directories
        temp_dir = os.path.join(base_dir, "temp")
        user_id = tool_context.state.get("user_id", "UNKNOWN_USER")
        pattern = rf"tia_responses_{user_id}__DATE-(\d{{8}}_\d{{6}})\.json"
        latest_file = None
        latest_dt = None

        for fname in os.listdir(temp_dir):
            match = re.match(pattern, fname)
            if match:
                dt_str = match.group(1)
                dt = datetime.strptime(dt_str, "%Y%m%d_%H%M%S")
                if latest_dt is None or dt > latest_dt:
                    latest_dt = dt
                    latest_file = fname

        if latest_file is None:
            return {"status": "error", "message": "No conversation history found."}
        filename = os.path.join(temp_dir, latest_file)
        with open(filename, 'r') as f:
            user_history = json.load(f)
        return {"status": "success", "user_history": user_history }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def store_user_profile(tool_context: ToolContext):
    """Store the generated user profile"""
    try:
        state = tool_context.state
        # JOSHUA TODO - Find a way to delete User_History from the state
        #del state["User_History"]
        profile = state.get("Generated_Profile")

        # INSERT ADD TO SQL NODE OR GNN CODE HERE

        return {"status": "success", "profile": profile}
    except Exception as e:
        return {"status": "error", "message": str(e)}

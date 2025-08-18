from google.adk.tools import ToolContext
from datetime import datetime
import os, json, re

def collect_user_history():
    """Find the user's most recent conversation history from tia_responses__DATE-*.json files."""
    try:
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        temp_dir = os.path.join(parent_dir, "temp")
        pattern = r"DATE-(\d{8}_\d{6})\.json"
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
        return user_history
    except Exception as e:
        return {"status": "error", "message": str(e)}

def store_user_profile(tool_context: ToolContext):
    """Store the generated user profile"""
    try:
        state = tool_context.state
        profile = state.get("Generated_Profile")

        # INSERT ADD TO SQL NODE OR GNN CODE HERE

        return {"status": "success", "profile": profile}
    except Exception as e:
        return {"status": "error", "message": str(e)}

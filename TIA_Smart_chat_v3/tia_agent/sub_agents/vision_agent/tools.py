from google.adk.tools.tool_context import ToolContext
from typing import Dict, Any
from dotenv import load_dotenv
from .utils import generate_content_blog, generate_content_messaging, generate_content_why_statement
from ...shared_state import get_or_create_assistant
import json

load_dotenv()



def generate_blog(tool_context: ToolContext) -> dict:
    """
    Generate all blog content using the three separate prompts.
    Arguments:
        user_responses: List of dicts with user responses (phase, message, etc.)
    Returns:
        dict: {
            "status": "success" or "error",
            "output": blog_output or error message,
            "filename": saved filename (if success)
        }
    """
    try:
        state = tool_context.state
        if "VisionAgent" not in state:
            state["VisionAgent"] = {}


        # TODO: INCLUDE THE LIMITED USER PROFILE ALWAYS
        vision_state = state["VisionAgent"]
        session_id = state.get("session_id")
        profile = state.get("Generated_Profile", None)
        
        if vision_state.get("chat_state") != "chat":
            print("DEBUG: Generating blog with existing profile")
            collected_context = state.get("Generated_Profile", None)
            collected_context.join("\n\n" + (f"User Profile Information:\n{json.dumps(profile, indent=2)}" if profile else "No user profile information available."))
        else:
            print("DEBUG: Generating blog with session_id:", session_id)
            user_id = state.get("user_id")
            assistant = get_or_create_assistant(session_id, user_id, "profiler:VisionAgent")

            collected_context = "\n".join([
                f"Phase {resp['phase']}: {resp['message']}"
                for resp in assistant.user_responses
            ])
            collected_context.join("\n\n" + (f"User Profile Information:\n{json.dumps(profile, indent=2)}" if profile else "No user profile information available."))

        vision_state["chat_state"] = "exit"
        if collected_context is None:
            return {"status": "error", "output": "No context collected."}

        # Generate the blog content
        results = []
        try:
            why_statement = generate_content_why_statement(collected_context)
            results.append("\n\n---\n\n## WHY STATEMENT\n\n---\n\n" + why_statement + "\n\n\n\n")
        except Exception as e:
            results.append(f"\n\n**Error generating Why Statement:** {e}\n\n\n\n")
        try:
            messaging = generate_content_messaging(collected_context)
            results.append("\n\n---\n\n## MESSAGING\n\n---\n\n" + messaging + "\n\n\n\n")
        except Exception as e:
            results.append(f"\n\n**Error generating Messaging:** {e}\n\n\n\n")
        try:
            content = generate_content_blog(collected_context)
            results.append("\n\n---\n\n## CONTENT\n\n---\n\n" + content + "\n\n\n\n")
        except Exception as e:
            results.append(f"\n\n**Error generating Content:** {e}\n\n\n\n")

        blog_output = "\n\n\n".join(results)
        blog_output = blog_output.replace('\n', '\n\n')

        state["user_profile"] = "collected"
        state["VisionAgent"] = vision_state
        return {
            "status": "success",
            "output": blog_output
        }
    except Exception as e:
        return {
            "status": "error",
            "output": f"Failed to generate blog: {e}"
        }
    
def start_dynamic_chat(tool_context: ToolContext) -> Dict[str, Any]:
    """Start a dynamic chat session with the Vision assistant"""
    try:
        state = tool_context.state
        vision_state = state.get("VisionAgent", {})
        if vision_state.get("chat_state") == "exit":
            return {"status": "error", "message": "Chat session has already ended.", "chat_state": "exit"}
        
        chat = vision_state["chat_state"] = "chat"
        state["VisionAgent"] = vision_state
        return {"status": "success", "chat_state": chat}
    except Exception as e:
        return {"status": "error", "message": str(e), "chat_state": chat}
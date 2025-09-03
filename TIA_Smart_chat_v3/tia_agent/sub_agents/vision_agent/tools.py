from google.adk.tools.tool_context import ToolContext
from ..DynamicChatAssistant import DynamicChatAssistant, generate_response
from typing import Dict, Any
import uuid
from datetime import datetime
from dotenv import load_dotenv

from .prompts import (
    DYNAMIC_CHAT_RULE_PROMPT,
    TIA_VISION_CHAT_1_FOUNDATION_PROMPT,
    TIA_VISION_CHAT_2_REFLECTION_PROMPT,
    TIA_VISION_CHAT_3_ANALYSIS_PROMPT,
    TIA_VISION_CHAT_4_STRATEGY_PROMPT,
    TIA_VISION_BLOG_1_WHY_STATEMENT_PROMPT,
    TIA_VISION_BLOG_2_MESSAGING_PROMPT,
    TIA_VISION_BLOG_3_CONTENT_PROMPT
)

load_dotenv()

BLOG_AMOUNT = 1
CHAT_PROMPTS = [
    TIA_VISION_CHAT_1_FOUNDATION_PROMPT,
    #TIA_VISION_CHAT_2_REFLECTION_PROMPT, 
    #TIA_VISION_CHAT_3_ANALYSIS_PROMPT,
    #TIA_VISION_CHAT_4_STRATEGY_PROMPT
]

# JOSHUA - TODO: IMPLENENT SESSION ID CONNECTION TO DB
# JOSHUA - TODO: FIX FORGOT LAST MESSAGE BUG AFTER EXIT
_user_sessions = {}

def get_or_create_assistant(session_id: str, user_id: int = None):
    """Get or create an assistant instance for a specific session."""
    global _user_sessions

    if not session_id:
        session_id = str(uuid.uuid4())

    # If the session doesn't exist, create a new assistant
    if session_id not in _user_sessions:
        assistant = DynamicChatAssistant(CHAT_PROMPTS, DYNAMIC_CHAT_RULE_PROMPT, user_id)
        assistant.session_id = session_id
        _user_sessions[session_id] = assistant

    return _user_sessions[session_id]

def _generate_content_why_statement(collected_context):
    """Generate Why Statement using collected responses"""
    why_prompt = TIA_VISION_BLOG_1_WHY_STATEMENT_PROMPT.format(collected_context=collected_context)
    input_messages = [
        {"role": "system", "content": why_prompt},
        {"role": "user", "content": "Please generate my Why Statement based on the context provided."}
    ]
    return generate_response(input_messages)

def _generate_content_messaging(collected_context):
    """Generate messaging (taglines, slogans, bios) using collected responses"""
    messaging_prompt = TIA_VISION_BLOG_2_MESSAGING_PROMPT.format(collected_context=collected_context)
    input_messages = [
        {"role": "system", "content": messaging_prompt},
        {"role": "user", "content": "Please generate messaging elements including taglines, slogans, and bio based on the context."}
    ]
    return generate_response(input_messages)

def _generate_content_blog(collected_context, blog_amount=BLOG_AMOUNT):
    """Generate blog content and social captions using collected responses"""
    all_content = []
    for i in range(blog_amount):
        print(f"[Generating content batch {i+1}/{blog_amount}]")
        content_prompt = TIA_VISION_BLOG_3_CONTENT_PROMPT.format(collected_context=collected_context)
        input_messages = [
            {"role": "system", "content": content_prompt},
            {"role": "user", "content": f"Please generate blog content batch {i+1} with social media captions based on the context."}
        ]
        assistant_response = generate_response(input_messages)
        all_content.append(f"\n{'='*20} CONTENT BATCH {i+1} {'='*20}\n{assistant_response}")
    return "\n".join(all_content)

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
        vision_state = state["VisionAgent"]
        session_id = vision_state.get("session_id")
        if session_id is None:
            return {"status": "error", "output": "No session ID found."}
        assistant = get_or_create_assistant(session_id)

        collected_context = "\n".join([
            f"Phase {resp['phase']}: {resp['message']}"
            for resp in assistant.user_responses
        ])

        if not collected_context.strip():
            warning = "No user responses found to generate blog content."
            print("⚠️ WARNING: No context collected from user responses!")
            return {"status": "error", "output": warning}

        results = []
        try:
            why_statement = _generate_content_why_statement(collected_context)
            results.append("WHY STATEMENT:\n" + "="*50 + "\n" + why_statement + "\n")
        except Exception as e:
            results.append(f"Error generating Why Statement: {e}\n")
        try:
            messaging = _generate_content_messaging(collected_context)
            results.append("MESSAGING:\n" + "="*50 + "\n" + messaging + "\n")
        except Exception as e:
            results.append(f"Error generating Messaging: {e}\n")
        try:
            content = _generate_content_blog(collected_context)
            results.append("CONTENT:\n" + "="*50 + "\n" + content + "\n")
        except Exception as e:
            results.append(f"Error generating Content: {e}\n")

        blog_output = "\n".join(results)
        filename = None

        # Clear the session
        _user_sessions[session_id] = None
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            blog_filename = f"blog_output_{timestamp}.txt"
            with open(blog_filename, 'w', encoding='utf-8') as f:
                f.write(f"Blog Generated: {datetime.now().isoformat()}\n")
                f.write("="*80 + "\n\n")
                f.write(blog_output)
            print(f"Blog output saved to {blog_filename}")
            filename = blog_filename
        except Exception as e:
            print(f"Error saving blog output: {e}")
            # Still return success, but note file save error
            return {
                "status": "success",
                "output": blog_output,
                "filename": None,
                "file_error": str(e)
            }

        return {
            "status": "success",
            "output": blog_output,
            "filename": filename
        }
    except Exception as e:
        return {
            "status": "error",
            "output": f"Failed to generate blog: {e}"
        }

def start_new_conversation(tool_context: ToolContext) -> Dict[str, Any]:
    """Start anew chat but if existing session, continue it"""
    try:
        state = tool_context.state
        user_id = state.get("user_id", "UNKNOWN_USER")
        print(f"USER ID: {user_id}")
        if "VisionAgent" not in state:
            state["VisionAgent"] = {}
        vision_state = state["VisionAgent"]
        session_id = vision_state.get("session_id", None)

        assistant = get_or_create_assistant(session_id, user_id)
        print(f"DEBUG: Chat session with ID: {assistant.session_id}")
        session_id = vision_state["session_id"] = assistant.session_id

        chat_state = vision_state["chat_state"] = "chat"
        current_phase = vision_state["current_phase"] = assistant.current_phase
        total_phases = vision_state["total_phases"] = len(assistant.prompts) - 1

        response = assistant.send_message("Help me Build my Vision")

        return {"status": "success", 
                "session_id": session_id, 
                "chat_state": chat_state, 
                "response": response, 
                "phase": current_phase, 
                "total_phases": total_phases
                }
    except Exception as e:
        return {"status": "error", "message": str(e), "chat_state": "exit"}

def chat_with_phases(user_input: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Return message from the dynamic TIA assistant chat"""
    try:
        state = tool_context.state
        vision_state = state["VisionAgent"]

        if vision_state is None:
            raise ValueError("VisionAgent state is not initialized.")
        session_id = vision_state.get("session_id", None)
        assistant = get_or_create_assistant(session_id)

        chat_state = vision_state.get("chat_state")
        current_phase = vision_state.get("current_phase")
        total_phases = vision_state.get("total_phases")
        
        if user_input.lower() in ['quit', 'exit', 'bye', 'end session', 'reset']:
            chat_state = vision_state["chat_state"] = "exit"
            assistant.save_responses()
            return {"status": "success", "chat_state": chat_state}
        
        response = assistant.send_message(user_input)

        current_phase = assistant.current_phase
        vision_state["current_phase"] = current_phase

        state["VisionAgent"] = vision_state
        if "<exit>" in response:
            chat_state = vision_state["chat_state"] = "exit"
            state["user_profile"] = "collected"
            state["VisionAgent"] = vision_state
            tool_context.actions.transfer_to_agent = "CoordinatorAgent"
            return {"status": "success", 
                    "chat_state": chat_state, 
                    "response": response
                    }

        return {"status": "success", 
                "session_id": session_id, 
                "chat_state": chat_state, 
                "response": response, 
                "current_phase": current_phase, 
                "total_phases": total_phases
                }
    
    except Exception as e:
        return {"status": "error", "message": str(e), "chat_state": "exit"}
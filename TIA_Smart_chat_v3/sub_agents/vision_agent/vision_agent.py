import json
import re
import logging
from datetime import datetime
from dotenv import load_dotenv
from litellm import completion
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from ..DynamicChatAssistant import DynamicChatAssistant, generate_response
from ...config import AGENT_MODEL, CHAT_MODEL, OPENAI_API_KEY
from .vision_prompts import (
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

BLOG_AMOUNT = 3
CHAT_PROMPTS = [
    TIA_VISION_CHAT_1_FOUNDATION_PROMPT,
    #TIA_VISION_CHAT_2_REFLECTION_PROMPT, 
    # TIA_VISION_CHAT_3_ANALYSIS_PROMPT,
    # TIA_VISION_CHAT_4_STRATEGY_PROMPT
]

from typing import Dict, Any
import uuid

# JOSHUA - TODO: IMPLENENT SESSION ID CONNECTION TO DB
# JOSHUA - TODO: FIX FORGOT LAST MESSAGE BUG AFTER EXIT
_user_sessions = {}

def get_or_create_assistant(session_id: str):
    """Get or create an assistant instance for a specific session"""
    global _user_sessions
    print(f"DEBUG SESSION: {_user_sessions}")
    
    if session_id is None or session_id not in _user_sessions:
        print(f"DEBUG: {session_id} not found, creating new assistant instance")
        unique_id = str(uuid.uuid4())
        assistant = DynamicChatAssistant(CHAT_PROMPTS, DYNAMIC_CHAT_RULE_PROMPT)
        assistant.session_unique_id = unique_id
        _user_sessions[session_id] = assistant
        print(f"DEBUG: Created new session with ID: {unique_id}")
    
    print(f"DEBUG SESSION AFTER: {_user_sessions}")
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
        session_id = state.get("session_id")
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

def start_session_phases(tool_context: ToolContext) -> Dict[str, Any]:
    """Start anew chat but if existing session, continue it"""
    try:
        state = tool_context.state
        session_id = state.get("session_id", None)

        assistant = get_or_create_assistant(session_id)
        print(f"DEBUG: Chat session with ID: {assistant.session_unique_id}")
        session_id = state["session_id"] = assistant.session_unique_id

        chat_state = state["chat_state"] = "chat"
        current_phase = state["current_phase"] = assistant.current_phase
        total_phases = state["total_phases"] = len(assistant.prompts) - 1

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
        session_id = state.get("session_id", None)
        assistant = get_or_create_assistant(session_id)
        session_id = state.get("session_id")

        chat_state = state.get("chat_state")
        current_phase = state.get("current_phase")
        total_phases = state.get("total_phases")
        
        if user_input.lower() in ['quit', 'exit', 'bye', 'end session', 'reset']:
            chat_state = state["chat_state"] = "exit"
            assistant.save_responses()
            return {"status": "success", "chat_state": chat_state}
        
        response = assistant.send_message(user_input)

        current_phase = assistant.current_phase
        state["current_phase"] = current_phase
        
        if "<exit>" in response:
            chat_state = state["chat_state"] = "exit"
            return {"status": "success", 
                    "chat_state": chat_state, 
                    "response": response
                    }

        return {"status": "success", 
                "session_id": session_id, 
                "chat_state": chat_state, 
                "response": response, 
                "phase": current_phase, 
                "total_phases": total_phases
                }
    
    except Exception as e:
        return {"status": "error", "message": str(e), "chat_state": "exit"}

chat_summary_prompt = """
    The TIA process guides users through multiple phases:
    1. Foundation - Core business concepts
    2. Generation - Content creation and implementation
    3. Reflection - Deep thinking about values and purpose  
    4. Analysis - Market and competitive analysis
    5. Strategy - Strategic planning and positioning
    6. Generation - Content creation and implementation
    """
    
    
VisionAgent = Agent(
    name="VisionAgent", 
    model=AGENT_MODEL,
    instruction=f"""
    You are the Dynamic TIA Assistant, guiding users through a multi-phase business vision process.

    **Your tools:**
    - Use `start_session_phases` only to begin a new session.
    - Use `chat_with_phases` for every user message during the session.

    **Rules:**
    - Always return tool outputs exactly as given—never add commentary or modify them.
    - Keep users engaged and moving through all phases; never answer for the user.
    - After each phase, ask if the user wants to continue to the next phase.

    **Session management:**
    - If `chat_state` is "exit":
        1. Immediately call `generate_blog` with the user's responses.
        2. Output the blog result to the user, exactly as returned.
        3. Then use `transfer_to_agent` to return to the CoordinatorAgent, passing the blog output.
        4. Do not transfer until after outputting the blog.
    - If `chat_state` is not "exit", continue using `chat_with_phases`.
    - Only use `start_session_phases` to start new sessions, not to resume.

    {chat_summary_prompt}

    After all phases, comprehensive business content is generated. Your job is to facilitate this journey and keep the conversation flowing naturally.
    """,
    tools=[start_session_phases, chat_with_phases, generate_blog]
)
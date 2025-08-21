from dotenv import load_dotenv
from litellm import completion
from urllib.parse import urlencode
from typing import Dict, Any, List
from google.adk.tools.tool_context import ToolContext
from ..DynamicChatAssistant import DynamicChatAssistant
import os, requests, json, http.client, uuid
from ...config import CHAT_MODEL, OPENAI_API_KEY, RAPIDAPI_HOST, RAPIDAPI_KEY
from .prompts import (
    CONNECT_RULE_PROMPT,
    CONNECT_CHAT_1_BUSINESS_INFO_PROMPT,
    CONNECT_GENERATION_PROMPT
)

load_dotenv()

CONNECT_PROMPTS = [
    CONNECT_CHAT_1_BUSINESS_INFO_PROMPT
]

_user_sessions = {}

def get_or_create_assistant(session_id: str, user_id: int = None):
    """Get or create an assistant instance for a specific session."""
    global _user_sessions

    if not session_id:
        session_id = str(uuid.uuid4())

    # If the session doesn't exist, create a new assistant
    if session_id not in _user_sessions:
        assistant = DynamicChatAssistant(CONNECT_RULE_PROMPT, CONNECT_CHAT_1_BUSINESS_INFO_PROMPT, user_id)
        assistant.session_id = session_id
        _user_sessions[session_id] = assistant

    return _user_sessions[session_id]

def recommended_GNN_connection(attributes: List[Dict[str, Any]]):
    """
    Connects to a GNN service to retrieve company context.
    Expects attributes to contain User, Idea, UserPost, and Strength.
    """
    return None
    # Prepare the payload
    payload = {
        "User": attributes.get("User"),
        "Idea": attributes.get("Idea"),
        "UserPost": attributes.get("UserPost"),
        "Strength": attributes.get("Strength")
    }

    # GNN endpoint URL
    gnn_url = os.getenv("GNN_API_URL", "http://localhost:8000/gnn/context")

    try:
        response = requests.post(gnn_url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()  # Return the company context from GNN
    except Exception as e:
        print(f"Error connecting to GNN: {e}")
        return None
    
def search_businesses_in_area(business_type: str, limit: int, region: str, zoom: int, lat: float, lng: float, language: str = "en",) -> dict:
    params = {
        "query": business_type,
        "lat": f"{lat:.6f}",
        "lng": f"{lng:.6f}",
        "limit": str(limit),
        "language": language,
        "region": region,
        "zoom": zoom,
        "extract_emails_and_contacts": str(True).lower(),
    }

    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY,
    }

    conn = http.client.HTTPSConnection(RAPIDAPI_HOST, timeout=30)
    try:
        path = f"/search-in-area?{urlencode(params)}"
        conn.request("GET", path, headers=headers)
        res = conn.getresponse()
        body = res.read()
        if res.status != 200:
            raise RuntimeError(f"HTTP {res.status}: {body.decode('utf-8', 'ignore')}")
        return json.loads(body)
    finally:
        conn.close()

def recommended_WEB_connection(attributes: Dict[str, Any]) -> dict:
    """
    Fallback: Uses LLM to turn attributes into a business query, then searches RapidAPI.
    """
    business_type = attributes.get("business_type", "")
    region = attributes.get("region", "au")
    lat = attributes.get("lat", 0.0)
    lng = attributes.get("lng", 0.0)
    limit = 5
    zoom = 10

    # Compose a prompt for the LLM to generate a business query string
    message = [
        {"role": "system", "content": "You are an assistant that generates concise business search queries for local business data APIs."},
        {"role": "user", "content": f"Attributes: {json.dumps(attributes.get("profile"))}\nTurn these into a business search query string for finding relevant businesses."}
    ]
    query = completion(
        model=CHAT_MODEL,
        messages=message,
        api_key=OPENAI_API_KEY
    ).choices[0].message.content.strip()

    try:
        results = search_businesses_in_area(query, limit, region, zoom, lat, lng)
        return results
    except Exception as e:
        print(f"Error in recommended_WEB_connection: {e}")
        return {"error": str(e)}

def recommended_connection(tool_context: ToolContext):
    try:
        state = tool_context.state
        required_keys = ["user_id", "region", "lat", "lng", "Generated_Profile"]
        missing = [k for k in required_keys if state.get(k) is None]
        if missing:
            return {"status": "error", "message": f"Missing required attributes: {', '.join(missing)}"}
        
        attributes = {
            "user_id": state.get("user_id"),
            "region": state.get("region"),
            "lat": state.get("lat"),
            "lng": state.get("lng"),
            "profile": state.get("Generated_Profile"),
        }
        GNN_CALL = recommended_GNN_connection(attributes)
        if GNN_CALL != None: return GNN_CALL

        WEB_CALL = recommended_WEB_connection(attributes)
        return WEB_CALL
    
    except Exception as e:
        print(f"Error in recommended_connection: {e}")

def start_new_conversation(tool_context: ToolContext) -> Dict[str, Any]:
    """Start a new SmartConnect session"""
    try:
        state = tool_context.state
        state["ConnectAgent"] = {}

        user_id = state.get("user_id", "UNKNOWN_USER")
        connect_state = state["ConnectAgent"]
        session_id = connect_state.get("session_id", None)
        print(f"DEBUG: start_session_phases called with session_id={session_id}")

        assistant = get_or_create_assistant(session_id, user_id)
        print(f"DEBUG: Chat session with ID: {assistant.session_unique_id}")
        session_id = connect_state["session_id"] = assistant.session_unique_id

        chat_state = connect_state["chat_state"] = "chat"
        current_phase = connect_state["current_phase"] = assistant.current_phase
        phase_prompt = connect_state["phase_prompt"] = assistant.system_prompt
        total_phases = connect_state["total_phases"] = len(assistant.prompts) - 1

        response = assistant.send_message("Lets Begin!")

        return {"status": "success", 
                "session_id": session_id, 
                "chat_state": chat_state, 
                "response": response, 
                "phase": current_phase, 
                "phase_prompt": phase_prompt,
                "total_phases": total_phases
                }
    except Exception as e:
        return {"status": "error", "message": str(e), "chat_state": "exit"}

def chat_with_phases(user_input: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Chat with the SmartConnect assistant"""
    try:
        state = tool_context.state
        connect_state = state["ConnectAgent"]
        session_id = connect_state.get("session_id", None)
        print(f"DEBUG: start_session_phases called with session_id={session_id}")
        assistant = get_or_create_assistant(session_id)
        session_id = connect_state.get("session_id")

        chat_state = connect_state["chat_state"] = "chat"
        current_phase = connect_state.get("current_phase")
        total_phases = connect_state.get("total_phases")
        
        if user_input.lower() in ['quit', 'exit', 'bye', 'end session', 'reset']:
            chat_state = connect_state["chat_state"] = "exit"
            assistant.save_responses()
            return {"status": "success", "chat_state": chat_state}
        
        response = assistant.send_message(user_input)

        current_phase = connect_state["current_phase"] = assistant.current_phase
        phase_prompt = connect_state["phase_prompt"] = assistant.system_prompt
        
        connect_state = state["ConnectAgent"]
        if current_phase > total_phases:
            chat_state = connect_state["chat_state"] = "exit"
            _user_sessions[session_id] = None
            connect_state = state["ConnectAgent"]
            return {"status": "success", 
                    "chat_state": chat_state, 
                    "response": response
                    }

        return {"status": "success", 
                "session_id": session_id,
                "chat_state": chat_state, 
                "response": response, 
                "phase": current_phase, 
                "phase_prompt": phase_prompt,
                "total_phases": total_phases
                }
    except Exception as e:
        return {"status": "error", "message": str(e), "chat_state": "exit"}
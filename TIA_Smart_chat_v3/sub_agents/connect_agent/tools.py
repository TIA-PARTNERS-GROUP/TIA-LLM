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
CITY_COORDS = {
    "brisbane": (-27.4698, 153.0251),
    "brisbane cbd": (-27.4679, 153.0281),
}

def search_businesses_in_area(business_type: str,
                              area: str = "Brisbane",
                              *,
                              limit: int = 20,
                              language: str = "en",
                              region: str = "au",
                              zoom: int = 13,
                              extract_emails_and_contacts: bool = False,
                              lat: float | None = None,
                              lng: float | None = None) -> dict:
    if lat is None or lng is None:
        key = area.strip().lower()
        if key not in CITY_COORDS:
            raise ValueError(
                f"Unknown area '{area}'. Provide lat/lng or add it to CITY_COORDS."
            )
        lat, lng = CITY_COORDS[key]

    params = {
        "query": business_type,
        "lat": f"{lat:.6f}",
        "lng": f"{lng:.6f}",
        "zoom": str(zoom),
        "limit": str(limit),
        "language": language,
        "region": region,
        "extract_emails_and_contacts": str(extract_emails_and_contacts).lower(),
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

def get_or_create_assistant(session_id: str):
    """Get or create an assistant instance for a specific session"""
    global _user_sessions
    print(f"DEBUG SESSION: {_user_sessions}")
    
    if session_id is None or session_id not in _user_sessions:
        print(f"DEBUG: {session_id} not found, creating new assistant instance")
        unique_id = str(uuid.uuid4())
        assistant = DynamicChatAssistant(CONNECT_PROMPTS, CONNECT_RULE_PROMPT)
        assistant.session_unique_id = unique_id
        _user_sessions[session_id] = assistant
        print(f"DEBUG: Created new session with ID: {unique_id}")
    
    print(f"DEBUG SESSION AFTER: {_user_sessions}")
    return _user_sessions[session_id]

def recommended_GNN_connection(attributes: List[Dict[str, Any]]):
    """
    Connects to a GNN service to retrieve company context.
    Expects attributes to contain User, Idea, UserPost, and Strength.
    """
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

def recommended_WEB_connection(attributes: Dict[str, Any]) -> dict:
    """
    Fallback: Uses LLM to turn attributes into a business query, then searches RapidAPI.
    """
    # Compose a prompt for the LLM to generate a business query string
    message = [
        {"role": "system", "content": "You are an assistant that generates concise business search queries for local business data APIs."},
        {"role": "user", "content": f"Attributes: {json.dumps(attributes)}\nTurn these into a business search query string for finding relevant businesses."}
    ]
    query = completion(
        model=CHAT_MODEL,
        messages=message,
        api_key=OPENAI_API_KEY
    ).choices[0].message.content.strip()

    # TODO: Make dynamic
    area = attributes.get("area", "Brisbane")
    limit = int(attributes.get("limit", 20))

    try:
        results = search_businesses_in_area(query, area, limit=limit)
        return results
    except Exception as e:
        print(f"Error in recommended_WEB_connection: {e}")
        return {"error": str(e)}

def recommended_connection(attributes: List[Dict[str, Any]], tool_context: ToolContext):
    try:
        GNN_CALL = recommended_GNN_connection(attributes)
        if GNN_CALL != None: return GNN_CALL

        WEB_CALL = recommended_WEB_connection(attributes)
        return WEB_CALL
    
    except Exception as e:
        print(f"Error in recommended_connection: {e}")

def grab_user_profile():
    return -1


#REMOVE at some point
#=========================================================================================
def start_session_phases(tool_context: ToolContext) -> Dict[str, Any]:
    """Start a new SmartConnect session"""
    try:
        state = tool_context.state
        session_id = state.get("session_id", None)
        print(f"DEBUG: start_session_phases called with session_id={session_id}")

        assistant = get_or_create_assistant(session_id)
        print(f"DEBUG: Chat session with ID: {assistant.session_unique_id}")
        session_id = state["session_id"] = assistant.session_unique_id

        chat_state = state["chat_state"] = "chat"
        current_phase = state["current_phase"] = assistant.current_phase
        phase_prompt = state["phase_prompt"] = assistant.system_prompt
        total_phases = state["total_phases"] = len(assistant.prompts) - 1

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
        session_id = state.get("session_id", None)
        print(f"DEBUG: start_session_phases called with session_id={session_id}")
        assistant = get_or_create_assistant(session_id)
        session_id = state.get("session_id")

        chat_state = state["chat_state"] = "chat"
        current_phase = state.get("current_phase")
        total_phases = state.get("total_phases")
        
        if user_input.lower() in ['quit', 'exit', 'bye', 'end session', 'reset']:
            chat_state = state["chat_state"] = "exit"
            assistant.save_responses()
            return {"status": "success", "chat_state": chat_state}
        
        response = assistant.send_message(user_input)

        current_phase = state["current_phase"] = assistant.current_phase
        phase_prompt = state["phase_prompt"] = assistant.system_prompt
        
        if current_phase > total_phases:
            chat_state = state["chat_state"] = "exit"
            _user_sessions[session_id] = None
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
#=========================================================================================
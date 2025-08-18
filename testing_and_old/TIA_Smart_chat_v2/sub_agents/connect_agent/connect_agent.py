from datetime import datetime
from dotenv import load_dotenv
from litellm import completion
from urllib.parse import urlencode
import os
import re
import json
import logging
import http.client
import uuid
import requests
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from typing import Dict, Any, List, Optional
from ...config import AGENT_MODEL, CHAT_MODEL, OPENAI_API_KEY, RAPIDAPI_HOST, RAPIDAPI_KEY
from .connect_prompts import (
    CONNECT_RULE_PROMPT,
    CONNECT_CHAT_1_BUSINESS_INFO_PROMPT,
    CONNECT_GENERATION_PROMPT
)

load_dotenv()

CONNECT_PROMPTS = [
    CONNECT_CHAT_1_BUSINESS_INFO_PROMPT
]

class DynamicChatAssistant:
    def __init__(self, prompts: list, rule_prompt: str):
        # Phase tracking, user history and responses
        self.current_phase = 0
        self.prompts = prompts
        self.rule_prompt = rule_prompt
        self.conversation_history = []
        self.user_responses = []
        self.system_prompt = self._get_wrapped_prompt(0)
        self.assistant_response = "" # Set first reply to empty string
        self.business_info = {}
        self.end_chat_session = False

        # Log file setup
        log_file = f"conversation_connect_chat_history.log"

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
    def _get_wrapped_prompt(self, phase_index):
        """Wrap the chat prompt with the connect rule prompts"""
        chat_prompt = self.prompts[phase_index]
        return self.rule_prompt.format(chat_prompt=chat_prompt)

    def _generate_response(self, message):
        response = completion(
            model=CHAT_MODEL,
            messages=message,
            api_key=OPENAI_API_KEY
        )
        return response.choices[0].message.content    

    def _next_phase(self):
        """Move to next phase - generate partner matches"""
        max_phase = len(self.prompts) - 1
        if self.current_phase < max_phase:
            self.current_phase += 1
            self.system_prompt = self._get_wrapped_prompt(self.current_phase)
            self.conversation_history.clear()
            print()
            print(f"[Moved to Phase {self.current_phase}] - Conversation history cleared")
            return None
        if self.current_phase == max_phase:
            print("[Generating blog content]")
            self.conversation_history.clear()
            self.save_responses()
            self.end_chat_session = True
            return None

    def send_message(self, message):
        """Send message using litellm with chosen API and record user response"""
        # Record user response
        self.user_responses.append({
            'phase': self.current_phase,
            'question': self.assistant_response,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
        self.conversation_history.append({
            "role": "user", 
            "content": message
        })
        
        input_messages = [
            {"role": "system", "content": self.system_prompt},
            *self.conversation_history
        ]

        self.logger.info("=" * 20)
        self.logger.info(f"*self.conversation_history: {self.conversation_history}")
        self.logger.info("=" * 20)

        self.assistant_response = self._generate_response(input_messages)

        self.conversation_history.append({
            "role": "assistant", 
            "content": self.assistant_response
        })
        
        # Check if the response contains the end tag
        end_tag = r'<\s*END_OF_TIA_PROMPT\s*>'
        if re.search(end_tag, self.assistant_response):
            self.assistant_response = re.sub(end_tag, '', self.assistant_response).strip()
            self.conversation_history[-1]["content"] = self.assistant_response
        
        return self.assistant_response
    
    def save_responses(self, id=None):
        """Save responses to JSON file"""
        if id is None:
            id = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"TIA_Smart_chat_v2/temp/tia_responses_{id}.json"

        with open(filename, 'w') as f:
            json.dump(self.user_responses, f, indent=2)
        print(f"Responses saved to {filename}")
        return filename
    

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
        assistant = DynamicChatAssistant(CONNECT_PROMPTS)
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

connect_summary_prompt = """
The TIA SmartConnect process guides users through:
1. Business Information Collection - Name, services, target market, unique value
2. Partner Match Generation - 4 ideal partner categories with email templates

SmartConnect helps small tech businesses find referral partners for mutual growth.
"""

ConnectAgent = Agent(
    name="ConnectAgent", 
    model=AGENT_MODEL,
    instruction=f"""
    You are the TIA SmartConnect Assistant, specialized in helping small tech businesses find ideal referral partners.
    
    Your role:
    - Use the `start_session_phases` tool to start a new SmartConnect session only.
    - Use the `chat_with_phases` function for EVERY user message during the conversation
    - Use the `recommended_connection` tool to generate partner connections once the chat is complete
    - Always maintain the conversation flow and encourage continued engagement
    - Return exactly what the tool gives you - do not add your own commentary
    - Keep users engaged in the partner matching process
    - Never answer for the user always wait for the users input

    **Tool Usage Flow:**
    1. `start_session_phases` - Initialize a new SmartConnect session
    2. `chat_with_phases` - Handle all user messages during business info collection
    3. `recommended_connection` - Generate partner matches after chat completion

    For tool `chat_with_phases` and `start_session_phases` usage:
    - `response` provides what you should return to the user
    - `session_id` is the unique identifier for the user's session
    - `phase` indicates the current phase of the conversation
    - `total_phases` indicates how many phases are in the conversation
    - `chat_state` indicates session status:
      - "chat": continue conversation
      - "exit": session ended, return to coordinator

    For `recommended_connection` usage:
    - Call this tool when chat_state becomes "complete" or when business info collection is finished
    - Pass the collected business attributes as parameters
    - This generates the 4 ideal partner categories with email templates

    **CRITICAL RULES**: 
    - When the `chat_state` is "exit", IMMEDIATELY stop and use the `transfer_to_agent` tool to return to the coordinatorAgent
    - When the `chat_state` is "complete", call `recommended_connection` to generate partner matches
    - When business info collection is finished, call `recommended_connection` before ending

    State management:
    - If you see `chat_state` is "exit", your task is complete and you should return to the coordinatorAgent
    - If `chat_state` is "chat", continue the conversation using the `chat_with_phases` tool
    - Use `start_session_phases` only to initialize a new session, not for resuming existing ones

    {connect_summary_prompt}
    
    Your job is to facilitate finding ideal referral partners, collect business information, generate connections, and keep the conversation flowing naturally.
    """,
    tools=[start_session_phases, chat_with_phases, recommended_connection]
)

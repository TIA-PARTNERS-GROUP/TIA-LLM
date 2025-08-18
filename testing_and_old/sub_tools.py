from google.adk.agents import BaseAgent, LlmAgent, LoopAgent, SequentialAgent, Agent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
import json, os, re, datetime
import logging

CONVERSATION_HISTORY_FILE = "/home/joshua/tia_connect/conversation_history.json"

def load_conversation_history():
    """Load existing conversation history from JSON file"""
    if os.path.exists(CONVERSATION_HISTORY_FILE):
        try:
            with open(CONVERSATION_HISTORY_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []

def save_conversation_entry(phase, question, answer):
    """Save a conversation entry to the JSON file"""
    history = load_conversation_history()
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "phase": phase,
        "question": question,
        "answer": answer
    }
    
    history.append(entry)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(CONVERSATION_HISTORY_FILE), exist_ok=True)
    
    with open(CONVERSATION_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)
    
    return f"Conversation entry saved for phase: {phase}"

def phase_checker_tool(text: str) -> str:
    """
    Tool that checks if the current phase should end based on <END_OF_TIA_PROMPT> tag
    """
    try:
        end_tag_pattern = r'<END_OF_TIA_PROMPT>'
        has_end_tag = bool(re.search(end_tag_pattern, text, re.IGNORECASE))
        
        if has_end_tag:
            return "PHASE_END"
        else:
            return "PHASE_CONTINUE"
        
    except Exception as e:
        logging.error(f"Error in phase_checker_tool: {str(e)}")
        return f"ERROR: {str(e)}"
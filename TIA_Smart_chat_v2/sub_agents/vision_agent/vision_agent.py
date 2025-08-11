import json
import re
import logging
from datetime import datetime
from dotenv import load_dotenv
from litellm import completion
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
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
    TIA_VISION_CHAT_2_REFLECTION_PROMPT, 
    # TIA_VISION_CHAT_3_ANALYSIS_PROMPT,
    # TIA_VISION_CHAT_4_STRATEGY_PROMPT
]

class AssistantWrapper:
    def __init__(self):
        # Phase tracking, user history and responses
        self.current_phase = 0
        self.prompts = CHAT_PROMPTS
        self.conversation_history = []
        self.user_responses = []
        self.system_prompt = self._get_wrapped_prompt(0)  # Load first prompt wrapped
        self.assistant_response = "" # Set first reply to empty string
            
        # Log file setup
        log_file = f"conversation_dynamic_chat_history.log"

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
    def _get_wrapped_prompt(self, phase_index):
        """Wrap the chat prompt with the dynamic rule prompts"""
        chat_prompt = self.prompts[phase_index]
        return DYNAMIC_CHAT_RULE_PROMPT.format(chat_prompt=chat_prompt)

    def _generate_response(self, message):
        response = completion(
            model=CHAT_MODEL,
            messages=message,
            api_key=OPENAI_API_KEY
        )
        return response.choices[0].message.content


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
            next_phase_result = self._next_phase()
            if next_phase_result:
                return self.assistant_response + "\n\n" + next_phase_result
        
        return self.assistant_response
    
    def _next_phase(self):
        """Move to next phase"""
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
            return self.generate_blog()
    
    def _generate_content_why_statement(self, collected_context):
        """Generate Why Statement using collected responses"""
        why_prompt = TIA_VISION_BLOG_1_WHY_STATEMENT_PROMPT.format(collected_context=collected_context)
        
        input_messages = [
            {"role": "system", "content": why_prompt},
            {"role": "user", "content": "Please generate my Why Statement based on the context provided."}
        ]
        
        assistant_response = self._generate_response(input_messages)
        
        return assistant_response
    
    def _generate_content_messaging(self, collected_context):
        """Generate messaging (taglines, slogans, bios) using collected responses"""
        messaging_prompt = TIA_VISION_BLOG_2_MESSAGING_PROMPT.format(collected_context=collected_context)
        
        input_messages = [
            {"role": "system", "content": messaging_prompt},
            {"role": "user", "content": "Please generate messaging elements including taglines, slogans, and bio based on the context."}
        ]
        
        assistant_response = self._generate_response(input_messages)
        return assistant_response

    def _generate_content_blog(self, collected_context):
        """Generate blog content and social captions using collected responses"""
        all_content = []
        
        for i in range(BLOG_AMOUNT):
            print(f"[Generating content batch {i+1}/{BLOG_AMOUNT}]")
            
            content_prompt = TIA_VISION_BLOG_3_CONTENT_PROMPT.format(collected_context=collected_context)
            
            input_messages = [
                {"role": "system", "content": content_prompt},
                {"role": "user", "content": f"Please generate blog content batch {i+1} with social media captions based on the context."}
            ]

            assistant_response = self._generate_response(input_messages)
            all_content.append(f"\n{'='*20} CONTENT BATCH {i+1} {'='*20}\n{assistant_response}")
        
        return "\n".join(all_content)
    
    def generate_blog(self):
        """Generate all blog content using the three separate prompts"""
        
        # Format all responses into context
        # Joshua - test replacing with user_responses later
        collected_context = "\n".join([
            f"Phase {resp['phase']}: {resp['message']}" 
            for resp in self.user_responses
        ])
        

        if not collected_context.strip():
            print("⚠️ WARNING: No context collected from user responses!")
            return "No user responses found to generate blog content."
        
        results = []
        
        # Generate Why Statement
        try:
            why_statement = self._generate_content_why_statement(collected_context)
            results.append("WHY STATEMENT:\n" + "="*50 + "\n" + why_statement + "\n")
        except Exception as e:
            results.append(f"Error generating Why Statement: {e}\n")
        
        # Generate Messaging
        try:
            messaging = self._generate_content_messaging(collected_context)
            results.append("MESSAGING:\n" + "="*50 + "\n" + messaging + "\n")
        except Exception as e:
            results.append(f"Error generating Messaging: {e}\n")
        
        # Generate Content
        try:
            content = self._generate_content_blog(collected_context)
            results.append("CONTENT:\n" + "="*50 + "\n" + content + "\n")
        except Exception as e:
            results.append(f"Error generating Content: {e}\n")
        
        # Combine all results
        blog_output = "\n".join(results)
        
        # Log the blog output to file
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            blog_filename = f"blog_output_{timestamp}.txt"
            with open(blog_filename, 'w', encoding='utf-8') as f:
                f.write(f"Blog Generated: {datetime.now().isoformat()}\n")
                f.write("="*80 + "\n\n")
                f.write(blog_output)
            print(f"Blog output saved to {blog_filename}")
        except Exception as e:
            print(f"Error saving blog output: {e}")
        
        return blog_output
    
    def save_responses(self, id=None):
        """Save responses to JSON file"""
        if id is None:
            id = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tia_responses_{id}.json"
            
        with open(filename, 'w') as f:
            json.dump(self.user_responses, f, indent=2)
        print(f"Responses saved to {filename}")
        return filename
    
    # For testing purposes
    def chat_loop(self):
        """Start an interactive chat session"""
        print("TIA Assistant Chat Session Started")
        print("Type 'quit', 'exit', or 'bye' to end")
        
        try:
            while True:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("Goodbye!")
                    self.save_responses()
                    break
                
                if not user_input:
                    continue
                
                print("Assistant is thinking...")
                try:
                    response = self.send_message(user_input)
                    print(f"Assistant: {response}\n")
                except Exception as e:
                    print(f"Error: {e}\n")
        
        except KeyboardInterrupt:
            print("\nChat session ended.")
            self.save_responses()

from typing import Dict, Any
import uuid

# JOSHUA - TODO: IMPLENENT SESSION ID CONNECTION TO DB
# JOSHUA - TODO: FIX FORGOT LAST MESSAGE BUG AFTER EXIT
_user_sessions = {}

def get_or_create_assistant(session_id: str):
    """Get or create an assistant instance for a specific session"""
    global _user_sessions
    
    if session_id not in _user_sessions or _user_sessions[session_id] is None:
        print(f"DEBUG: {session_id} not found, creating new assistant instance")
        unique_id = str(uuid.uuid4())
        assistant = AssistantWrapper()
        assistant.session_unique_id = unique_id
        _user_sessions[session_id] = assistant
        print(f"DEBUG: Created new session with ID: {unique_id}")
    
    return _user_sessions[session_id]

def start_chat_session(tool_context: ToolContext) -> Dict[str, Any]:
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

def chat_with_tia(user_input: str, tool_context: ToolContext) -> Dict[str, Any]:
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
                "total_phases": total_phases
                }
    
    except Exception as e:
        return {"status": "error", "message": str(e), "chat_state": "exit"}

chat_summary_prompt = """
    The TIA process guides users through multiple phases:
    1. Foundation - Core business concepts
    2. Reflection - Deep thinking about values and purpose  
    3. Analysis - Market and competitive analysis
    4. Strategy - Strategic planning and positioning
    """
    
VisionAgent = Agent(
    name="VisionAgent", 
    model=AGENT_MODEL,
    instruction=f"""
    You are the Dynamic TIA Assistant, specialized in guiding users through a comprehensive business vision development process.
    
    Your role:
    - Use the `start_chat_session` tool to start a new chat only.
    - Use the `chat_with_tia` function for EVERY user message
    - Always maintain the conversation flow and encourage continued engagement
    - Return exactly what the tool gives you - do not add your own commentary
    - Keep users engaged in developing their business vision through all phases
    - Never answer for the user always wait for the users input

    For tool `chat_with_tia` and `chat_with_tia` usage:
    - `response` provides what you should return to the user
    - `session_id` is the unique identifier for the user's session
    - `phase` indicates the current phase of the conversation
    - `total_phases` indicates how many phases are in the conversation
    - `chat_state` indicates if the user has ended the session. True means your the session is over and return to the coordinatorAgent, False means continue the conversation

    **CRITICAL RULES**: 
    - When the `chat_state` is "exit", IMMEDIATELY stop and use the `transfer_to_agent` tool to return to the coordinatorAgent

    State management:
    - If you see `chat_state` is "exit", your task for now is complete and you should return to the coordinatorAgent
    - If `chat_state` is False, continue the conversation using the `chat_with_tia` tool
    - Use `start_chat_session` only to initialize a new session, not for resuming existing ones

    {chat_summary_prompt}
    
    After each phase ask the user if they want to continue to the next phase.
    After all phases, comprehensive business content is generated.
    Your job is to facilitate this journey and keep the conversation flowing naturally.
    """,
    tools=[start_chat_session, chat_with_tia]
)

# https://cloud.google.com/blog/topics/developers-practitioners/tools-make-an-agent-from-zero-to-assistant-with-adk
# https://cloud.google.com/blog/topics/developers-practitioners/remember-this-agent-state-and-memory-with-adk

# # event.py
# # in_memory_session_service.py
# # state.py
# # https://www.youtube.com/watch?v=ZqLdpiMMCnM
# # https://www.youtube.com/watch?v=J6BUAUy5KsQ
# from google.adk.sessions import InMemorySessionService, state
# from google.adk.events import Event
# import uuid
# import threading

# app_name = "TIA_Smart_chat_v2"
# _local = threading.local()

# def get_or_create_session_info():
#     """Get or create session info for this thread/user"""
#     if not hasattr(_local, 'user_id'):
#         # First time for this thread - create new session info
#         thread_id = threading.current_thread().ident
#         unique_id = str(uuid.uuid4())
        
#         _local.user_id = f"user_{thread_id}_{unique_id}"
#         _local.session_id = f"session_{thread_id}_{unique_id}"
        
#         print(f"DEBUG: Created new session info for thread {thread_id}")
    
#     return _local.user_id, _local.session_id

# async def chat_with_tia(user_input: str, **kwargs):
#     """Persistent TIA conversation function using ADK session management"""
#     session_service = InMemorySessionService()
    
#     # Get consistent session info for this thread/user
#     #user_id, session_id = get_or_create_session_info()
#     user_id = "1"
#     session_id = "2"
    
#     print(f"DEBUG: user_id = {user_id}")
#     print(f"DEBUG: session_id = {session_id}")

#     try:
#         # Try to get existing session
#         session = await session_service.get_session(
#             app_name=app_name,
#             user_id=user_id, 
#             session_id=session_id
#         )
        
#         # If no session exists, create one
#         if not session:
#             session = await session_service.create_session(
#                 app_name=app_name,
#                 user_id=user_id,
#                 session_id=session_id,
#                 state={"assistant_data": None}
#             )
#             print(f"DEBUG: Created new ADK session {session.id}")
#         else:
#             print(f"DEBUG: Using existing ADK session {session.id}")
        
#         # Get or create AssistantWrapper from session state
#         if session.state.get("assistant_data"):
#             # Recreate AssistantWrapper from saved state
#             assistant = AssistantWrapper()
#             assistant.current_phase = session.state["assistant_data"].get("current_phase", 0)
#             assistant.conversation_history = session.state["assistant_data"].get("conversation_history", [])
#             assistant.user_responses = session.state["assistant_data"].get("user_responses", [])
#             assistant.assistant_response = session.state["assistant_data"].get("assistant_response", "")
#             assistant.system_prompt = assistant._get_wrapped_prompt(assistant.current_phase)
#             print(f"DEBUG: Restored assistant from session - Phase {assistant.current_phase}")
#         else:
#             # Create new AssistantWrapper
#             assistant = AssistantWrapper()
#             print(f"DEBUG: Created new AssistantWrapper")
        
#         # Handle quit commands
#         if user_input.lower() in ['quit', 'exit', 'bye', 'end session', 'reset']:
#             assistant.save_responses(session.id)
#             # Clear the session
#             await session_service.delete_session(app_name, user_id, session_id)
#             # Clear thread-local storage so next message starts fresh
#             # if hasattr(_local, 'user_id'):
#             #     delattr(_local, 'user_id')
#             # if hasattr(_local, 'session_id'):
#             #     delattr(_local, 'session_id')
#             return "TIA session ended. Thank you for using TIA! Start a new conversation anytime."
        
#         response = assistant._send_message(user_input)
        
#         # Update session state directly
#         session.state["assistant_data"] = {
#             "current_phase": assistant.current_phase,
#             "conversation_history": assistant.conversation_history,
#             "user_responses": assistant.user_responses,
#             "assistant_response": assistant.assistant_response
#         }
        
#         # # Create a proper Event to persist the state (optional - the state is already updated above)
#         # from google.adk.events import Event, EventActions
        
#         # state_update_event = Event(
#         #     author="TIA_StateManager",
#         #     content=None,  # No content needed for state updates
#         #     actions=EventActions()  # Empty actions is fine
#         # )
        
#         # # Append the event (this will trigger state persistence)
#         # await session_service.append_event(session, state_update_event)

#         print(f"DEBUG: State: {session.state['assistant_data']}")
        
#         # Add phase information
#         current_phase = assistant.current_phase
#         total_phases = len(assistant.prompts) - 1
        
#         if current_phase <= total_phases:
#             phase_info = f"\n\n📍 Phase {current_phase + 1}/{total_phases + 1} of your business vision journey."
#             response += phase_info
        
#         return response
        
#     except Exception as e:
#         print(f"ERROR in chat_with_tia: {e}")
#         import traceback
#         traceback.print_exc()
#         return f"Sorry, I encountered an error: {str(e)}. Please try again."


# class DynamicTIAAgent(BaseAgent):
#     """
#     Dynamic TIA Agent that wraps the AssistantWrapper for use in the ADK.
#     This agent handles individual message exchanges, not chat loops.
#     """
    
#     # Pydantic field declarations
#     model_config = {"arbitrary_types_allowed": True}
    
#     def __init__(self, name="DynamicTIAAgent", **kwargs):
#         super().__init__(name=name, **kwargs)
#         self._assistant_wrapper = None
    
#     @property
#     def assistant_wrapper(self):
#         """Lazy initialization of assistant wrapper"""
#         if self._assistant_wrapper is None:
#             self._assistant_wrapper = AssistantWrapper()
#         return self._assistant_wrapper
    
#     async def _run_async_impl(self, ctx: InvocationContext):
#         """Handle continuous TIA conversation flow - provides clear continuation"""
        
#         try:
#             # Extract user message from context
#             user_message = None
            
#             # Try different methods to extract the message
#             try:
#                 if hasattr(ctx, 'session') and hasattr(ctx.session, 'messages') and ctx.session.messages:
#                     last_msg = ctx.session.messages[-1]
#                     if last_msg.role == 'user':
#                         user_message = last_msg.content.parts[0].text
#             except Exception:
#                 pass
            
#             if not user_message:
#                 try:
#                     if hasattr(ctx, 'message') and ctx.message:
#                         user_message = ctx.message.content.parts[0].text
#                 except Exception:
#                     pass
            
#             if not user_message:
#                 try:
#                     if hasattr(ctx, 'request') and hasattr(ctx.request, 'message'):
#                         user_message = ctx.request.message.content.parts[0].text
#                 except Exception:
#                     pass
            
#             # If no message found, start with welcome
#             if not user_message or not user_message.strip():
#                 user_message = "start"
            
#             # Check for session end commands
#             if user_message.lower() in ['quit', 'exit', 'bye', 'end session']:
#                 result = self._end_session()
#                 from google.genai import types
#                 yield Event(
#                     content=types.Content(
#                         role='model',
#                         parts=[types.Part(text=result)]
#                     ),
#                     author=self.name
#                 )
#                 return
            
#             # Process the message and get response
#             response = self.assistant_wrapper._send_message(user_message)
            
#             # Check current state and add continuation guidance
#             current_phase = self.assistant_wrapper.current_phase
#             total_phases = len(self.assistant_wrapper.prompts) - 1
            
#             if current_phase <= total_phases:
#                 # Still in conversation phases
#                 phase_status = f"\n\n[TIA Phase {current_phase + 1}/{total_phases + 1}] - Continue the conversation or type 'quit' to end session."
#                 response += phase_status
#             elif current_phase > total_phases:
#                 # Completed all phases
#                 response += "\n\n[TIA Complete] - Your business vision is fully developed! Continue chatting for refinements or type 'quit' to end."
            
#             # Send the response
#             from google.genai import types
#             yield Event(
#                 content=types.Content(
#                     role='model',
#                     parts=[types.Part(text=response)]
#                 ),
#                 author=self.name
#             )
                
#         except Exception as e:
#             import traceback
#             error_detail = traceback.format_exc()
#             print(f"ERROR in TIA agent: {error_detail}")
#             from google.genai import types
#             yield Event(
#                 content=types.Content(
#                     role='model',
#                     parts=[types.Part(text=f"I encountered an error in our TIA session. Please try again or type 'quit' to end. Error: {str(e)[:100]}")]
#                 ),
#                 author=self.name
#             )
    
#     def _end_session(self):
#         """End the current session and return results"""
#         try:
#             filename = self.assistant_wrapper.save_responses()
#             total_responses = len(self.assistant_wrapper.user_responses)
#             final_phase = self.assistant_wrapper.current_phase
            
#             # Reset for next session
#             self._assistant_wrapper = None
            
#             return f"""TIA Session Ended!

#             Session Summary:
#             - Final Phase: {final_phase}/3
#             - Total Responses: {total_responses}
#             - Data saved to: {filename}

#             You can start a new TIA session anytime by sending another message."""
            
#         except Exception as e:
#             return f"Error ending session: {e}"
    
#     def get_session_status(self):
#         """Get current session status"""
#         if self._assistant_wrapper is None:
#             return "No active TIA session. Send a message to begin."
#         else:
#             phase = self.assistant_wrapper.current_phase
#             responses = len(self.assistant_wrapper.user_responses)
#             return f"Active TIA session - Phase: {phase}/3, Responses: {responses}"

# Testing in file
if __name__ == "__main__":
    """Main function to run the assistant"""
    try:
        assistant = AssistantWrapper()
        assistant.chat_loop()
    except Exception as e:
        print(f"Error: {e}")
        print("Please make an API key is set in your .env file.")
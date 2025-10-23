from litellm import completion
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types

from .tia_agent.shared_state import get_or_create_assistant
import os, uuid, logging, json

from .tia_agent.config import OPENAI_API_KEY
try:
    from .tia_agent.agent import coordinatorAgent
except ImportError:
    from tia_agent.agent import coordinatorAgent


# Load environment variables and setup logging
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize session service with MySQL
db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASS")
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")
db_port = os.getenv("DB_PORT")
db_url = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
session_service = DatabaseSessionService(db_url=db_url)

# Create runner
runner = Runner(
    agent=coordinatorAgent,
    app_name="tia_smart_chat",
    session_service=session_service
)

def _handle_chat_type(type: str):
    """
    Handles agent switching by sending a transfer message to the runner.
    Maps short agent names to full names and triggers the transfer.
    Supports format: 'default', 'profiler:<sub_type>', or 'connect:<connection_type>'
    """
    try:
        connection_type = None

        # Parse the input - chat type : connection type E.g. connect:complementary
        if ':' in type:
            agent_type, sub_type = type.split(':', 1)
        else:
            raise ValueError("Chat type must be in format 'profiler:<sub_type>' or 'connect:<connection_type>'")

        # Determine agent type
        if agent_type == "profiler":
            valid_profiler_types = ["VisionAgent", "LadderAgent"]
            if sub_type in valid_profiler_types:
                full_agent = sub_type
            else:
                raise ValueError(f"Invalid or missing profiler type. Must be one of {valid_profiler_types}.")
        elif agent_type == "connect":
            full_agent = "ConnectAgent"

            # Determine connection type for ConnectAgent
            valid_connection_types = ["complementary", "alliance", "mastermind", "intelligent"]
            
            if sub_type in valid_connection_types:
                connection_type = sub_type
            else:
                raise ValueError(f"Invalid or missing connection type for ConnectAgent. Must be one of {valid_connection_types}.")

            logger.debug(f"Set connection_type to '{connection_type}' before transfer")
        else:
            raise ValueError(f"Invalid agent type '{agent_type}'. Must be 'profiler', 'connect', or 'default'.")
        
        return full_agent, connection_type
    except Exception as e:
        logger.error("ERROR in handle_chat_type:", e)
        raise Exception("Error during agent switching: " + str(e))

async def _create_new_session(user_id: str, name: str, region: str, lat: float, lng: float, chat_type: str):
    """
    Creates a new session with initial state.
    """
    try:
        session_id = str(uuid.uuid4())
        full_agent, connection_type = _handle_chat_type(chat_type)
        logger.info(f"Creating new session with ID: {session_id}, Agent: {full_agent}, Connection Type: {connection_type}")
        state = {
            "name": name,
            "user_id": user_id,
            "session_id": session_id,
            "set_agent": full_agent,
            "connection_type": connection_type,
            "region": region,
            "lat": lat,
            "lng": lng,
            "end_session": False,
            "user_profile": "check",
        }
        session = await session_service.create_session(
            app_name="tia_smart_chat",
            user_id=user_id,
            session_id=session_id,
            state=state
        )
        return session
    except Exception as e:
        logger.error("ERROR in create_new_session:", e)
        raise Exception("Error creating new session: " + str(e))

async def _get_existing_session(user_id: str, session_id: str):
    """
    Retrieves an existing session by user_id and session_id.
    """
    try:
        session = await session_service.get_session(
            app_name="tia_smart_chat",
            user_id=user_id,
            session_id=session_id
        )
        return session
    except Exception as e:
        logger.error("ERROR in get_existing_session:", e)
        raise Exception("Error retrieving existing session: " + str(e))

async def run_chat(user_id: str, name: str, region: str, lat: float, lng: float, chat_type: str, message: str, session_id=None):
    """
    Runs a chat session, creating a new session if necessary.
    Handles agent transfers and session state updates.
    Returns the session, response text, and author.
    """
    try:
        author = None
        response_text = None
        if session_id is None:
            session = await _create_new_session(user_id, name, region, lat, lng, chat_type)
        else:
            # session_id provided: Try to get existing session
            session = await _get_existing_session(user_id, session_id)

            # session_id provided but doesn't exist: Create a new session
            if session is None:
                session = await _create_new_session(user_id, name, region, lat, lng, chat_type)

        # Prepare message
        new_message = types.Content(
            role="user",
            parts=[types.Part(text=message)]
        )

        # Handle agent transfer
        set_agent = session.state.get("set_agent")
        vision_state = session.state.get("VisionAgent", {})
        chat_state = vision_state.get("chat_state")
        
        # Determine if DynamicChatAssistant should handle the chat
        response_text = None
        if set_agent == "VisionAgent" and chat_state == "chat":
            chat_assistant = get_or_create_assistant(session.id, session.user_id, chat_type)
            response_text = chat_assistant.send_message(message)

            # Enforce exit condition
            if "<exit>" in response_text:
                response_text = None
            author = "DynamicChatAssistant"
            new_message = types.Content(
                    role="user",
                    parts=[types.Part(text="[DYNAMIC CHAT COMPLETED USE `generate_blog` TO CREATE BLOG]")] # Force the Agent to generate blog (NOTE: Workaround for LLM hallucinations)
                )

        # Return a google ADK runner response if DynamicChatAssistant did not handle it
        if response_text is None:
            for event in runner.run(
                user_id=session.user_id,
                session_id=session.id,
                new_message=new_message
            ):
                logger.debug(f"[CHAT EVENT]\nEvent: {event}\nSession ID: {session.id}\nState: {json.dumps(session.state, indent=2)}")
                
                if event.is_final_response() and event.content and event.content.parts:
                    response_text = event.content.parts[0].text
                    author = event.author
            
        # Get updated session state
        session = await _get_existing_session(user_id, session.id)
        set_agent = session.state.get("set_agent")
        logger.debug(f"Final session state after chat: {session.state}")
        logger.debug(f"Set Agent after chat: {set_agent}")

        if set_agent == "ProfilerAgent":
            auto_transfer_message = types.Content(
                    role="user",
                    parts=[types.Part(text="Use `transfer_to_agent` to switch to ProfilerAgent and gather user profile information.")]
                )
            for event in runner.run(
                user_id=session.user_id,
                session_id=session.id,
                new_message=auto_transfer_message
            ):
                logger.debug(f"Transfer Event: {event}")
        
        # Check if session should end
        session = await _get_existing_session(user_id, session.id)
        end_session = session.state.get("end_session", False)
        if end_session and set_agent:
            await delete_session(user_id, session.id)
            session = await _create_new_session(user_id, name, region, lat, lng, chat_type)

        # if "<SILENT_AGENT>" in response_text:
        #     response_text = "Chat Completed. Restarting session."
        #     await delete_session(user_id, session.id)
        #     session = await _create_new_session(user_id, name, region, lat, lng, chat_type)

        return session, response_text, author
    except Exception as e:
        logger.error("ERROR in run_chat:", e)
        raise Exception("Error during chat: " + str(e))

async def delete_session(user_id: str, session_id: str):
    """
    Deletes a session by user_id and session_id.
    """
    try:
        await session_service.delete_session(
            app_name="tia_smart_chat",
            user_id=user_id,
            session_id=session_id
        )
        logger.debug(f"Session {session_id} for user {user_id} deleted.")
    except Exception as e:
        logger.error("ERROR in delete_session:", e)
        raise Exception("Error deleting session: " + str(e))

def compare_responses(actual: str, expected: str) -> float:
    """
    Uses litellm to compare actual and expected responses by prompting an LLM to rate similarity.
    Returns a score from 0 to 10.
    """
    prompt = f"Rate the similarity between these two responses on a scale of 0 to 10, where 10 is identical and 0 is completely different. Only return the number as a float.\n\nActual: {actual}\n\nExpected: {expected}"
    
    try:
        response = completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            api_key=OPENAI_API_KEY,
            max_tokens=10,
            temperature=0.0
        )
        score_text = response.choices[0].message.content.strip()
        score = float(score_text)
        return max(0.0, min(10.0, score))
    except Exception as e:
        logger.error(f"Error in comparison: {e}")
        return 0.0
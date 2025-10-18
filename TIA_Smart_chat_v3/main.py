from fastapi import FastAPI, Request, HTTPException
from .utils import compare_responses, run_chat, delete_session
from dotenv import load_dotenv
import uuid, json, os, logging

load_dotenv()

# Logging setup
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    # Default to INFO
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('TIA-LLM.log')
    ]
)
logger = logging.getLogger(__name__)

# FastAPI app
# To run: uvicorn TIA_Smart_chat_v3.main:app --reload --port 8080
app = FastAPI()
CONVERSATIONS_DIR = os.path.join(os.getcwd(), "tmp", "agent_chat_history")

# Main Chat endpoint
@app.post("/chat/tia-chat")
async def chat_endpoint(requests: Request):
    data = await requests.json()
    try:
        logger.info("Received data: %s", data)
        user_id = str((data.get("user_id")))
        name = data.get("name")
        message = data.get("message")
        region = data.get("region", "au")
        lat = data.get("lat", 0.0)
        lng = data.get("lng", 0.0)
        chat_type = data.get("chat_type", "Default")
        session_id = data.get("session_id", None)
        save_conversation = data.get("save_conversation", False)

        session, response, author = await run_chat(user_id, name, region, lat, lng, chat_type, message, session_id)

        result = {
            "response": response,
            "session_id": session.id,   
            "state": dict(session.state),
            "author": author
        }

        # If save_conversation flag is true, save the conversation to a JSON file
        if save_conversation:
            new_entry = {
                "message": message,
                "response": response,
                "state": dict(session.state),
                "author": author,
                "timestamp": str(uuid.uuid4())
            }
            file_path = f"{CONVERSATIONS_DIR}/{session.id}.json"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    data = json.load(f)
                data["conversations"].append(new_entry)
            else:
                data = {
                    "session_id": session.id,
                    "user_id": user_id,
                    "conversations": [new_entry]
                }
            
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)
            result["saved_to"] = file_path

        logger.debug("Session state after chat: %s", session.state)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to reset a session
@app.post("/chat/reset-session")
async def reset_session(requests: Request):
    data = await requests.json()
    try:
        user_id = str((data.get("user_id")))
        session_id = data.get("session_id")
        if not user_id or not session_id:
            raise HTTPException(status_code=400, detail="user_id and session_id are required")
        await delete_session(user_id, session_id)

        return {"detail": "Session reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to test evaluation of conversations
@app.post("/chat/test-eval")
async def test_eval(requests: Request):
    data = await requests.json()
    try:
        expected = data.get("expected")
        if not expected:
            raise HTTPException(status_code=400, detail="expected is required")
        
        # Load data from the expected file
        if isinstance(expected, str) and os.path.isfile(expected):
            with open(expected, "r") as f:
                expected_data = json.load(f)
            conversations = expected_data.get("conversations", [])
            user_id = expected_data.get("user_id")
            if not conversations:
                raise HTTPException(status_code=400, detail="No conversations found in expected file")
        else:
            raise HTTPException(status_code=400, detail="expected must be a valid file path")
        
        # Run through conversations and compare responses
        scores = []
        total_score = 0
        session_id = None
        for i, conv in enumerate(conversations):
            message = conv.get("message")
            expected_response = conv.get("response")

            # Use the first conversation's details for name, region, etc., or load from state
            name = expected_data.get("name", "Unknown")
            region = expected_data.get("region", "au")
            lat = expected_data.get("lat", 0.0)
            lng = expected_data.get("lng", 0.0)
            
            session, actual_response, author = await run_chat(user_id, name, region, lat, lng, message, session_id)
            session_id = session.id
            
            # Compare using litellm
            score = compare_responses(actual_response, expected_response)
            scores.append({
                "index": i,
                "message": message,
                "actual_response": actual_response,
                "expected_response": expected_response,
                "score": score
            })
            total_score += score
        
        overall_score = total_score / len(scores) if scores else 0

        logger.debug("Test evaluation completed for %d conversations", len(scores))
        return {
            "overall_score": overall_score,
            "session_id": session_id,
            "state": dict(session.state) if session else {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

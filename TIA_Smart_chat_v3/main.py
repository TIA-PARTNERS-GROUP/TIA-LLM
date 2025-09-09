from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid, json, os
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.runners import RunConfig
from google.genai import types
from .utils import compare_responses

try:
    from .tia_agent.agent import coordinatorAgent
except ImportError:
    from tia_agent.agent import coordinatorAgent

# Load environment variables
load_dotenv()

# Initialize session service with MySQL
session_service = InMemorySessionService()

# Create runner
runner = Runner(
    agent=coordinatorAgent,
    app_name="tia_smart_chat",
    session_service=session_service
)

async def run_chat(user_id: str, name: str, region: str, lat: float, lng: float, message: str, session_id=None):
    try:
        if not session_id:
            session_id = str(uuid.uuid4())
            state = {
                "name": name,
                "user_id": user_id,
                "region": region,
                "lat": lat,
                "lng": lng,
                "user_profile": "n/a"
            }
            session = await session_service.create_session(
                app_name="tia_smart_chat",
                user_id=user_id,
                session_id=session_id,
                state=state
            )
        else:
            session = await session_service.get_session(
                app_name="tia_smart_chat",
                user_id=user_id,
                session_id=session_id
            )

        # Prepare message
        new_message = types.Content(
            role="user",
            parts=[types.Part(text=message)]
        )

        response_text = None
        for event in runner.run(
            user_id=session.user_id,
            session_id=session.id,
            new_message=new_message
        ):
            print("DEBUG: event =", event)
            if event.is_final_response() and event.content and event.content.parts:
                response_text = event.content.parts[0].text
                author = event.author

        if response_text is None:
            response_text = "No response generated."

        return session, response_text, author
    except Exception as e:
        print("ERROR in run_chat:", e)
        raise Exception("Error during chat: " + str(e))



# FastAPI app
app = FastAPI()
CONVERSATIONS_DIR = os.path.join(os.getcwd(), "tmp", "agent_chat_history")

# To run: uvicorn TIA_Smart_chat_v3.main:app --reload --port 8080
@app.post("/chat/tia-chat")
async def chat_endpoint(requests: Request):
    data = await requests.json()
    try:
        print("DEBUG: Received data =", data)
        user_id = str((data.get("user_id")))
        name = data.get("name")
        message = data.get("message")
        region = data.get("region", "au")
        lat = data.get("lat", 0.0)
        lng = data.get("lng", 0.0)
        session_id = data.get("session_id", None)
        save_conversation = data.get("save_conversation", False)

        session, response, author = await run_chat(user_id, name, region, lat, lng, message, session_id)

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

        print("DEBUG: Session state after chat:", session.state)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/chat/reset-session")
async def reset_session(requests: Request):
    data = await requests.json()
    try:
        user_id = str((data.get("user_id")))
        session_id = data.get("session_id")
        if not user_id or not session_id:
            raise HTTPException(status_code=400, detail="user_id and session_id are required")

        await session_service.delete_session(
            app_name="tia_smart_chat",
            user_id=user_id,
            session_id=session_id
        )
        return {"detail": "Session reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        
        scores = []
        total_score = 0
        session_id = None  # Start with no session for the first run
        
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
        
        print("DEBUG: Test evaluation completed for", len(scores), "conversations")
        return {
            "overall_score": overall_score,
            "session_id": session_id,
            "state": dict(session.state) if session else {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# CLI for testing
import asyncio
if __name__ == "__main__":
    user_id = input("User ID: ")
    name = input("Name: ")
    session_id = None
    region = "au" #input("Region: ")
    lat = 27.4705#float(input("Latitude: "))
    lng = 153.0245#float(input("Longitude: "))

    while True:
        message = input("Message (or 'exit' to quit): ")
        if message.lower() in ['exit', 'quit']:
            break

        session, response_text = asyncio.run(run_chat(user_id, name, region, lat, lng, message, session_id))
        print(f"\n\nResponse: {response_text}\nSession ID: {session.id}\n\n")
        session_id = session.id
        
        print("DEBUG: Session state:", session.state)

# @app.post("/chat/tia-chat")
# async def chat_endpoint(requests: Request):
#     data = await requests.json()
#     try:
#         print("DEBUG: Received data =", data)
#         user_id = str((data.get("user_id")))
#         name = data.get("name")
#         message = data.get("message")
#         region = data.get("region", "au")
#         lat = data.get("lat", 0.0)
#         lng = data.get("lng", 0.0)
#         session_id = data.get("session_id", None)

#         session, response = await run_chat(user_id, name, region, lat, lng, message, session_id)

#         print("DEBUG: Session state after chat:", session.state)
#         return {
#             "response": response,
#             "session_id": session.id,
#             "state": dict(session.state)
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

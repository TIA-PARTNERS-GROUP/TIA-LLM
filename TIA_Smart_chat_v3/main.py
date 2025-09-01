from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import os
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.runners import RunConfig
from google.genai import types

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

async def run_chat(user_id: str, name: str, message: str, session_id=None):
    try:
        if not session_id:
            session_id = str(uuid.uuid4())
            user_state = {"name": name, "user_id": user_id}
            session = await session_service.create_session(
                app_name="tia_smart_chat",
                user_id=user_id,
                session_id=session_id,
                state=user_state
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

        if response_text is None:
            response_text = "No response generated."

        return session, {"response": response_text, "session_id": session.id}
    except Exception as e:
        print("ERROR in run_chat:", e)
        raise Exception("Error during chat: " + str(e))



# FastAPI app
app = FastAPI()

# To run: uvicorn TIA_Smart_chat_v3.main:app --reload --port 8080
@app.post("/tia_chat")
async def chat_endpoint(requests: Request):
    data = await requests.json()
    try:
        user_id = data.get("user_id")
        name = data.get("name")
        message = data.get("message")
        print(f"DEBUG: Received message from user_id={user_id}, name={name}: {message}")
        session_id = data.get("session_id", None)

        session, result = await run_chat(user_id, name, message, session_id)
        return {
            "result": result,
            "session_id": session.id,
            "state": dict(session.state)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# CLI for testing
import asyncio
if __name__ == "__main__":
    user_id = input("User ID: ")
    name = input("Name: ")
    session_id = None

    while True:
        message = input("Message (or 'exit' to quit): ")
        if message.lower() in ['exit', 'quit']:
            break

        session, result = asyncio.run(run_chat(user_id, name, message, session_id))
        print(f"\n\nResponse: {result['response']}\nSession ID: {result['session_id']}\n\n")
        session_id = result['session_id']
        
        print("DEBUG: Session state:", session.state)
        
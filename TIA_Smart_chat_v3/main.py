from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import os
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types
from tia_agent.agent import coordinatorAgent

# Load environment variables
load_dotenv()

# Database configuration
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Initialize session service with MySQL
db_url = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
session_service = DatabaseSessionService(db_url=db_url)

# Create runner
runner = Runner(
    agent=coordinatorAgent,
    app_name="tia_smart_chat",
    session_service=session_service
)

# FastAPI app
app = FastAPI()

class ChatRequest(BaseModel):
    user_id: str
    name: str
    message: str

# Create a new session for each chat
@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    session_id = str(uuid.uuid4())
    user_state = {"name": req.name}

    # Create the session in DB
    await session_service.create_session(
        app_name="tia_smart_chat",
        user_id=req.user_id,
        session_id=session_id,
        state=user_state
    )

    # Prepare message
    new_message = types.Content(
        role="user",
        parts=[types.Part(text=req.message)]
    )

    # Run the agent
    response_text = ""
    for event in runner.run(
        user_id=req.user_id,
        session_id=session_id,
        new_message=new_message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text

    return {"response": response_text, "session_id": session_id}

# To run: uvicorn main:app --reload
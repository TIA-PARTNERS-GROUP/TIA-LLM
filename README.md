# TIA-LLM

TIA-LLM is an AI-powered chatbot system built with FastAPI and Google ADK for managing conversations, agent switching, and session handling. It utilizes Google ADK for general agentic actions and includes a dynamic chat object implemented under `DynamicChatAssistant` for handling conversational chains, such as those involving long questions.
<img width="2282" height="1252" alt="diagram_blizzard" src="https://github.com/user-attachments/assets/54855732-be78-40c3-87cb-c9c42c0e6c9f" />

## Setup

1. **Clone the repository** (if not already done):
   ```
   git clone <repository-url>
   cd tia_connect/TIA-LLM
   ```

2. **Create a virtual environment**:
   ```
   python -m venv .venv
   ```

3. **Activate the virtual environment**:
   - On Windows:
     ```
     .venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source .venv/bin/activate
     ```

4. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

## How to Launch

To run the application, use the following command (as noted in `main.py`):

```
uvicorn TIA_Smart_chat_v3.main:app --reload --port 8080
```

- `--reload`: Enables auto-reload on code changes (useful for development).
- `--port 8080`: Runs the server on port 8080.

The API will be available at `http://localhost:8080`.

### Endpoints

- `POST /chat/tia-chat`: Send a message to the chatbot.
- `POST /chat/reset-session`: Reset a user session.
- `POST /chat/test-eval`: Run evaluation tests.

## Additional Notes

- Ensure your database is set up and running (MySQL in this case).
- The app uses Google ADK for agent management and session persistence.
- Google ADK Web is excellent for Google visual web debugging, providing a graphical interface to inspect and debug agent interactions.
- Logs are saved to `TIA-LLM.log` in addition to being output to the terminal.
- The `tmp` directory is used for recording test cases when activated through the JS backend.

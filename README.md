# TIA-LLM

TIA-LLM is an AI-powered chatbot system built with FastAPI and Google ADK for managing conversations, agent switching, and session handling.

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

5. **Set up environment variables**:
   - Create a `.env` file in the root directory with necessary variables (e.g., database credentials, API keys).
   - Example:
     ```
     DB_USER=your_db_user
     DB_PASS=your_db_password
     DB_HOST=localhost
     DB_NAME=tiapartners
     DB_PORT=3333
     OPENAI_API_KEY=your_openai_key
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
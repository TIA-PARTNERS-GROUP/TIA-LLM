# TIA Smart Chat Assistant

## How to Run Your Assistant

Your assistant is now ready to use! Here's how to interact with it:

### Quick Start

1. **Navigate to the project directory:**
   ```bash
   cd /home/joshua/tia_connect/TIA_Smart_chat_v2
   ```

2. **Run the assistant:**
   ```bash
   /home/joshua/tia_connect/.venv/bin/python sub_agents/assistant_wrapper.py
   ```

### Features

- **Interactive Chat**: Type your messages and get responses from your OpenAI assistant
- **Environment Variables**: Automatically loads your API key and assistant ID from `.env` file
- **Thread Management**: Maintains conversation context throughout the session
- **Error Handling**: Graceful error handling and informative messages

### Usage Commands

- Type any message to chat with your assistant
- Type `quit`, `exit`, or `bye` to end the conversation
- Press `Ctrl+C` to force quit

### Environment Setup

Your `.env` file is already configured with:
- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_ASSISTANT_ID`: Your specific assistant ID

### Code Structure

The `AssistantWrapper` class provides:
- `create_thread()`: Creates a new conversation thread
- `send_message(message)`: Sends a message and gets the assistant's response
- `chat_loop()`: Starts an interactive chat session

### Example Usage

```python
from sub_agents.assistant_wrapper import AssistantWrapper

# Create and use the assistant
assistant = AssistantWrapper()

# Send a single message
response = assistant.send_message("Hello, how can you help me?")
print(response)

# Or start an interactive chat
assistant.chat_loop()
```

### Troubleshooting

If you encounter any issues:
1. Make sure your `.env` file contains valid API credentials
2. Check that the `openai` and `python-dotenv` packages are installed
3. Ensure you're using the correct Python environment path

Your assistant is ready to help with your TIA project needs!

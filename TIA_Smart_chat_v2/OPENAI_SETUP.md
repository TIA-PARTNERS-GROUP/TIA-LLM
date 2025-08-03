# OpenAI Assistant Setup Guide

## Yes! ADK doesn't have built-in OpenAI Assistant support, but I've created a complete implementation for you.

## 🎯 **What You Have Now:**

### **1. Real OpenAI Assistant Integration**
- Full `OpenAIAssistantWrapper` class that uses the OpenAI API
- Automatic thread management and conversation state tracking
- Error handling and fallback to mock for testing

### **2. Easy Configuration**
Set these environment variables:

```bash
# Required for real OpenAI Assistant
export OPENAI_API_KEY="your-openai-api-key"
export OPENAI_ASSISTANT_ID="asst_your_assistant_id"

# Optional - for testing
export USE_MOCK_ASSISTANT="false"  # Set to "true" for testing without API
```

## 🚀 **How to Use:**

### **Step 1: Install OpenAI Library**
```bash
pip install openai
```

### **Step 2: Create Your OpenAI Assistant**
1. Go to [OpenAI Platform](https://platform.openai.com/assistants)
2. Create a new Assistant
3. Configure it for business vision conversations
4. Copy the Assistant ID (starts with `asst_`)

### **Step 3: Set Environment Variables**
```bash
export OPENAI_API_KEY="sk-your-api-key"
export OPENAI_ASSISTANT_ID="asst_your_assistant_id"
```

### **Step 4: Use in Your Code**
```python
from TIA_Smart_chat_v2.agent import root_agent

# The system automatically detects your settings and uses:
# - Real OpenAI Assistant if API key and ID are provided
# - Mock assistant for testing if not

# Start a conversation
agent = root_agent
# Now you can use it with your ADK agents!
```

## 🔧 **Configuration Options:**

### **Use Real OpenAI Assistant:**
```python
from TIA_Smart_chat_v2.assistant_wrapper import OpenAIAssistantWrapper

# Direct usage
assistant = OpenAIAssistantWrapper(
    assistant_id="asst_your_id",
    api_key="sk-your-key"  # Optional if env var is set
)

thread_id = assistant.create_thread()
response = assistant.send_message(thread_id, "Hello!")
print(response["message"])
```

### **Use Mock for Testing:**
```python
from TIA_Smart_chat_v2.assistant_wrapper import MockAssistantWrapper

assistant = MockAssistantWrapper()
# Same interface, but mock responses
```

### **Factory Function (Recommended):**
```python
from TIA_Smart_chat_v2.assistant_wrapper import create_assistant_wrapper

# Automatically chooses based on environment
assistant = create_assistant_wrapper()

# Force mock for testing
assistant = create_assistant_wrapper(use_mock=True)

# Specify assistant ID directly
assistant = create_assistant_wrapper("asst_your_id")
```

## 📋 **Sample Assistant Instructions**

When creating your OpenAI Assistant, use these instructions:

```
You are a business vision consultant helping entrepreneurs explore and define their business purpose. 

Your role:
1. Ask thoughtful questions about their business, goals, and vision
2. Adapt questions based on their responses
3. Help them discover insights about their market, customers, and value proposition
4. Guide them toward clarity on their business purpose and next steps

Style:
- Be conversational and friendly
- Ask one question at a time
- Build on their previous answers
- Show genuine interest in their business journey

Start by greeting them and asking for their name, then naturally flow into exploring their business.
```

## 🔄 **Conversation Flow:**

1. **User starts conversation** → `GeneralChatAgent` greets
2. **User ready to begin** → `QuestionAgent` calls OpenAI Assistant
3. **Assistant asks dynamic questions** based on responses
4. **User answers** → `QuestionCheckerAgent` validates relevance
5. **If relevant** → Continue with Assistant
6. **If off-topic** → `GeneralChatAgent` redirects
7. **Assistant determines completion** and next steps

## 🛠️ **Advanced Features:**

### **Conversation History:**
```python
# Get conversation history
history = assistant.get_conversation_history(thread_id, limit=20)
for msg in history:
    print(f"{msg['role']}: {msg['content']}")
```

### **Custom Context:**
```python
# Pass additional context to assistant
context = {"user_industry": "tech", "company_size": "startup"}
response = assistant.send_message(thread_id, message, context)
```

### **Multiple Model Support:**
```python
# Use different models for different sessions
local_agent = create_agent_with_model("local", "qwen3:14b")
api_agent = create_agent_with_model("api", "gemini")
```

## 🎉 **You're All Set!**

Your TIA Smart Chat v2 now has:
- ✅ Real OpenAI Assistant integration
- ✅ Local Ollama model support  
- ✅ Cloud API model support (Gemini, GPT)
- ✅ Dynamic conversation flow
- ✅ Automatic fallback for testing
- ✅ Session management
- ✅ Error handling

Just set your `OPENAI_API_KEY` and `OPENAI_ASSISTANT_ID` and you're ready to go!

"""
Example demonstrating OpenAI Assistant integration with TIA Smart Chat v2
"""

import os
from TIA_Smart_chat_v2.assistant_wrapper import (
    create_assistant_wrapper, 
    OpenAIAssistantWrapper, 
    MockAssistantWrapper
)
from TIA_Smart_chat_v2.agent import root_agent, create_agent_with_model


def test_mock_assistant():
    """Test the mock assistant wrapper"""
    print("=== Testing Mock Assistant ===")
    
    # Create mock assistant
    assistant = MockAssistantWrapper()
    
    # Create thread and send messages
    thread_id = assistant.create_thread()
    print(f"Created thread: {thread_id}")
    
    # Send first message
    response1 = assistant.send_message(thread_id, "Hello, I'm ready to start!")
    print(f"Assistant: {response1['message']}")
    
    # Send follow-up
    response2 = assistant.send_message(thread_id, "My name is John")
    print(f"Assistant: {response2['message']}")
    
    # Check conversation state
    state = assistant.get_conversation_state(thread_id)
    print(f"Conversation state: {state}")


def test_real_assistant():
    """Test the real OpenAI Assistant (requires API key and Assistant ID)"""
    print("=== Testing Real OpenAI Assistant ===")
    
    api_key = os.getenv("OPENAI_API_KEY")
    assistant_id = os.getenv("OPENAI_ASSISTANT_ID")
    
    if not api_key or not assistant_id:
        print("❌ Missing OPENAI_API_KEY or OPENAI_ASSISTANT_ID")
        print("Set these environment variables to test real assistant")
        return
    
    try:
        # Create real assistant
        assistant = OpenAIAssistantWrapper(assistant_id, api_key)
        
        # Create thread and send message
        thread_id = assistant.create_thread()
        print(f"Created thread: {thread_id}")
        
        response = assistant.send_message(
            thread_id, 
            "Hello! I'm excited to explore my business vision with you."
        )
        
        print(f"Assistant: {response['message']}")
        print(f"Status: {response.get('status', 'unknown')}")
        
        # Get conversation history
        history = assistant.get_conversation_history(thread_id)
        print(f"Conversation history: {len(history)} messages")
        
    except Exception as e:
        print(f"❌ Error testing real assistant: {str(e)}")


def test_factory_function():
    """Test the assistant factory function"""
    print("=== Testing Factory Function ===")
    
    # Test automatic detection
    assistant = create_assistant_wrapper()
    print(f"Created assistant: {type(assistant).__name__}")
    
    # Test forced mock
    mock_assistant = create_assistant_wrapper(use_mock=True)
    print(f"Created mock assistant: {type(mock_assistant).__name__}")


def test_adk_integration():
    """Test integration with Google ADK agents"""
    print("=== Testing ADK Integration ===")
    
    # Test with different models
    print("Available configurations:")
    print("- Local Ollama models")
    print("- API models (Gemini, GPT)")
    print("- Mock vs Real OpenAI Assistant")
    
    # Example of using with ADK
    agent = root_agent
    print(f"Root agent created: {agent.name}")
    
    # Example with custom model
    local_agent = create_agent_with_model("local", "qwen3:14b")
    print(f"Local agent created with model: qwen3:14b")


def demonstrate_complete_flow():
    """Demonstrate the complete conversation flow"""
    print("=== Complete Flow Demonstration ===")
    
    # This would be the actual usage pattern
    print("1. User starts conversation")
    print("   → GeneralChatAgent greets and explains process")
    
    print("\n2. User indicates readiness")
    print("   → QuestionAgent calls OpenAI Assistant")
    print("   → Assistant asks first dynamic question")
    
    print("\n3. User responds")
    print("   → QuestionCheckerAgent validates relevance")
    print("   → If relevant: continue with Assistant")
    print("   → If off-topic: GeneralChatAgent redirects")
    
    print("\n4. Assistant adapts questions based on responses")
    print("   → Dynamic conversation flow")
    print("   → Context-aware follow-ups")
    
    print("\n5. Assistant determines completion")
    print("   → Provides summary or next steps")


def main():
    """Run all examples"""
    print("TIA Smart Chat v2 - OpenAI Assistant Integration Examples")
    print("=" * 60)
    
    # Test mock assistant (always works)
    test_mock_assistant()
    print()
    
    # Test factory function
    test_factory_function()
    print()
    
    # Test real assistant (if configured)
    test_real_assistant()
    print()
    
    # Test ADK integration
    test_adk_integration()
    print()
    
    # Demonstrate flow
    demonstrate_complete_flow()
    
    print("\n" + "=" * 60)
    print("🎉 OpenAI Assistant Integration Ready!")
    print("\nTo use with real OpenAI Assistant:")
    print("1. Set OPENAI_API_KEY environment variable")
    print("2. Set OPENAI_ASSISTANT_ID environment variable") 
    print("3. Install: pip install openai")
    print("4. Run your agent!")


if __name__ == "__main__":
    main()

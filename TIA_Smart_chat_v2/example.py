"""
Example usage of TIA Smart Chat v2 with OpenAI Assistant integration.

This demonstrates how to use the new dynamic chat system with both local and API models.
"""

import os
from TIA_Smart_chat_v2.agent import root_agent, create_agent_with_model
from TIA_Smart_chat_v2.utils import ConversationManager, switch_model, get_available_models
from TIA_Smart_chat_v2.assistant_wrapper import assistant_wrapper


def example_local_model():
    """Example using local Ollama model."""
    print("=== Local Model Example ===")
    
    # Use default local model (qwen3:14b)
    agent = root_agent
    
    # Or create with specific local model
    # agent = create_agent_with_model("local", "qwen2.5:7b")
    
    print("Local agent created with Ollama model")
    return agent


def example_api_model():
    """Example using API-based model (Gemini)."""
    print("=== API Model Example ===")
    
    # Switch to API model
    switch_model("api", "gemini")
    agent = create_agent_with_model("api", "gemini")
    
    print("API agent created with Gemini model")
    return agent


def example_conversation_manager():
    """Example using the conversation manager for multiple sessions."""
    print("=== Conversation Manager Example ===")
    
    manager = ConversationManager()
    
    # Create different sessions with different models
    local_agent = manager.create_session("local_session", "local", "qwen3:14b")
    api_agent = manager.create_session("api_session", "api", "gemini")
    
    print("Sessions created:")
    print(manager.list_sessions())
    
    # Switch between sessions
    manager.switch_session("local_session")
    print("Switched to local session")
    
    return manager


def example_assistant_wrapper():
    """Example showing how the assistant wrapper works."""
    print("=== Assistant Wrapper Example ===")
    
    # Create a conversation thread
    thread_id = assistant_wrapper.create_thread()
    print(f"Created thread: {thread_id}")
    
    # Send a message (this is what the agents will do internally)
    response = assistant_wrapper.send_message(
        thread_id=thread_id,
        message="Hello, I'm ready to start exploring my business vision.",
        context={}
    )
    
    print("Assistant response:", response)
    
    # Get conversation state
    state = assistant_wrapper.get_conversation_state(thread_id)
    print("Conversation state:", state)
    
    return thread_id


def simulate_conversation():
    """Simulate a full conversation flow."""
    print("=== Simulated Conversation Flow ===")
    
    # Create agent
    agent = root_agent
    
    # Simulate conversation state
    conversation_state = {}
    
    # Simulate user interactions
    user_messages = [
        "Hi there!",
        "My name is John",
        "I run a small consulting business",
        "We help startups with their marketing strategy"
    ]
    
    for message in user_messages:
        print(f"User: {message}")
        
        # In real usage, you'd call the agent with the message
        # result = agent.process(message, conversation_state)
        # print(f"Agent: {result}")
        
        # For demo, just show the flow
        print("Agent would process this message through:")
        print("1. QuestionCheckerAgent - validate relevance")
        print("2. QuestionAgent - get assistant response")
        print("3. Present response to user")
        print()


def main():
    """Main example function."""
    print("TIA Smart Chat v2 - Examples\n")
    
    # Show available models
    models = get_available_models()
    print("Available models:", models)
    print()
    
    # Run examples
    example_local_model()
    print()
    
    example_api_model()
    print()
    
    example_conversation_manager()
    print()
    
    example_assistant_wrapper()
    print()
    
    simulate_conversation()
    
    print("\n=== Setup Complete ===")
    print("Your TIA Smart Chat v2 is ready!")
    print("\nNext steps:")
    print("1. Implement your OpenAI Assistant wrapper")
    print("2. Replace MockAssistantWrapper with your implementation")
    print("3. Configure your preferred model (local/API)")
    print("4. Start conversations using the root_agent")


if __name__ == "__main__":
    main()

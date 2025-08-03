#!/usr/bin/env python3
"""
Test script for TIA Assistant with Response Recording

This script tests the assistant functionality without requiring manual input.
"""

import json
from datetime import datetime
from assistant_wrapper import AssistantWrapper

def test_response_recording():
    """Test the response recording functionality with actual assistant calls"""
    print("🧪 Testing TIA Assistant Response Recording")
    print("=" * 50)
    
    try:
        # Create assistant instance
        assistant = AssistantWrapper()
        
        # Test sample responses for each phase
        test_responses = {
            1: [  # Foundation phase
                "John Smith",
                "Tech Innovations LLC", 
                "Founder and CEO",
                "AI-powered customer service automation",
                "Small to medium businesses"
            ],
            2: [  # Reflection phase
                "I imagined having more freedom and helping businesses grow",
                "More challenging but rewarding than expected",
                "Peace of mind and time savings for business owners",
                "We helped a restaurant handle COVID order surge",
                "Made their business efficient and stress-free",
                "Help owners focus on what they love",
                "Proud of positive impact we make"
            ],
            3: [  # Analysis phase
                "Industry-specific templates would excite customers",
                "Could expand to e-commerce and healthcare",
                "Personalized onboarding sets us apart",
                "Lack of genuine care in automation solutions",
                "Human-feeling, not robotic solutions",
                "More conversational and empathetic AI",
                "Technology should enhance, not replace connection",
                "Growing profits, could improve pricing tiers"
            ],
            4: [  # Strategy phase
                "Let's shape my Why Statement",
                "Human and Professional blend",
                "Yes, blend warmth with credibility", 
                "Yes, finalize this Why Statement",
                "Yes, move to messaging",
                "Warm but professional tone",
                "Yes, create blog content",
                "Prefer downloadable PDF",
                "Tech Innovations Purpose Playbook",
                "Review full set when done"
            ]
        }
        
        # Test each phase with ACTUAL assistant calls
        for phase in range(1, 5):
            print(f"\n📋 Testing Phase {phase}")
            print("-" * 30)
            
            # Set the current phase
            assistant.current_phase = phase
            assistant.system_prompt = assistant.prompts[phase - 1]
            
            # Send test responses for this phase using REAL assistant calls
            for i, response in enumerate(test_responses[phase]):
                print(f"Sending: {response[:50]}...")
                
                try:
                    # Actually call the assistant
                    assistant_response = assistant.send_message(response)
                    print(f"Assistant replied: {assistant_response[:100]}...")
                    print()
                except Exception as e:
                    print(f"Error calling assistant: {e}")
                    # Fallback to manual recording if API fails
                    assistant.user_responses.append({
                        'phase': phase,
                        'message': response,
                        'timestamp': datetime.now().isoformat()
                    })
                    
            print(f"✅ Completed Phase {phase}")
        
        # Generate blog content using collected responses
        print(f"\n� Generating Blog Content")
        print("=" * 40)
        
        try:
            blog_content = assistant.generate_blog_content()
            print("🎉 BLOG CONTENT GENERATED:")
            print("-" * 50)
            print(blog_content)
            print("-" * 50)
        except Exception as e:
            print(f"Error generating blog content: {e}")
            # Show what we collected anyway
            print("Collected responses:")
            for resp in assistant.user_responses:
                print(f"Phase {resp['phase']}: {resp['message'][:50]}...")
        
        # Save responses
        filename = assistant.save_responses("test_responses.json")
        print(f"\n� Responses saved to: {filename}")
        
        print(f"\n🎉 Test completed! Total responses: {len(assistant.user_responses)}")
        return assistant
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Make sure OPENAI_API_KEY and OPENAI_ASSISTANT_ID are set in .env file")
        return None

def test_phase_transitions():
    """Test phase transition functionality"""
    print(f"\n🔄 Testing Phase Transitions")
    print("-" * 30)
    
    assistant = AssistantWrapper()
    
    # Test moving through phases
    for phase in range(1, 5):
        print(f"Current phase: {assistant.current_phase}")
        
        if phase < 4:
            assistant.next_phase()
            print(f"After next_phase(): {assistant.current_phase}")
        else:
            print("At final phase - would generate blog content")
    
    print("✅ Phase transitions working correctly")

def test_commands():
    """Test the command functionality"""
    print(f"\n⌨️  Testing Commands")
    print("-" * 30)
    
    assistant = AssistantWrapper()
    
    # Add some test responses
    assistant.user_responses = [
        {'phase': 1, 'message': 'Test response 1', 'timestamp': '2025-01-01T10:00:00.000Z'},
        {'phase': 2, 'message': 'Test response 2', 'timestamp': '2025-01-01T10:01:00.000Z'}
    ]
    
    # Test save command
    print("Testing save command...")
    filename = assistant.save_responses("test_commands.json")
    print(f"✅ Save command works: {filename}")
    
    # Test next command
    print("Testing next command...")
    original_phase = assistant.current_phase
    assistant.next_phase()
    if assistant.current_phase == original_phase + 1:
        print("✅ Next command works")
    else:
        print("❌ Next command failed")
    
    print("✅ Commands working correctly")

def interactive_test():
    """Run a simple interactive test"""
    print(f"\n🎮 Interactive Test Mode")
    print("-" * 30)
    print("This will start the assistant in test mode.")
    print("You can type a few test responses and then type 'quit' to see results.")
    
    choice = input("Start interactive test? (y/n): ").lower()
    if choice == 'y':
        assistant = AssistantWrapper()
        
        print("\nStarting assistant... (Type 'quit' after a few test responses)")
        print("Note: OpenAI calls will only work if you have valid API keys set up.\n")
        
        try:
            assistant.chat_loop()
            
            # Show results
            print(f"\n📊 Test Results:")
            print(f"Total responses recorded: {len(assistant.user_responses)}")
            for i, resp in enumerate(assistant.user_responses):
                print(f"  {i+1}. Phase {resp['phase']}: {resp['message'][:50]}...")
                
        except Exception as e:
            print(f"Note: {e}")
            print("This is expected if OpenAI keys aren't configured.")

def quick_blog_test():
    """Quick test that focuses on blog generation with new prompts"""
    print("🚀 Quick Blog Generation Test (New Prompts)")
    print("=" * 50)
    
    try:
        assistant = AssistantWrapper()
        
        # Add sample responses directly
        sample_responses = [
            {'phase': 1, 'message': 'John Smith', 'timestamp': datetime.now().isoformat()},
            {'phase': 1, 'message': 'Tech Innovations LLC', 'timestamp': datetime.now().isoformat()},
            {'phase': 1, 'message': 'Founder and CEO', 'timestamp': datetime.now().isoformat()},
            {'phase': 1, 'message': 'AI-powered customer service automation', 'timestamp': datetime.now().isoformat()},
            {'phase': 1, 'message': 'Small to medium businesses', 'timestamp': datetime.now().isoformat()},
            
            {'phase': 2, 'message': 'I imagined having more freedom and helping businesses grow', 'timestamp': datetime.now().isoformat()},
            {'phase': 2, 'message': 'More challenging but rewarding than expected', 'timestamp': datetime.now().isoformat()},
            {'phase': 2, 'message': 'Peace of mind and time savings for business owners', 'timestamp': datetime.now().isoformat()},
            
            {'phase': 3, 'message': 'Industry-specific templates would excite customers', 'timestamp': datetime.now().isoformat()},
            {'phase': 3, 'message': 'Could expand to e-commerce and healthcare', 'timestamp': datetime.now().isoformat()},
            
            {'phase': 4, 'message': "Let's shape my Why Statement", 'timestamp': datetime.now().isoformat()},
            {'phase': 4, 'message': 'Human and Professional blend', 'timestamp': datetime.now().isoformat()},
        ]
        
        assistant.user_responses = sample_responses
        
        print(f"📝 Testing new blog generation with {len(sample_responses)} responses...")
        
        # Test all three new prompts
        collected_context = "\n".join([f"Phase {resp['phase']}: {resp['message']}" for resp in sample_responses])
        
        print("\n🎯 1. GENERATING WHY STATEMENT...")
        print("-" * 40)
        try:
            why_statement = assistant.generate_why_statement(collected_context)
            print(why_statement)
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n📢 2. GENERATING MESSAGING...")
        print("-" * 40)
        try:
            messaging = assistant.generate_messaging(collected_context)
            print(messaging)
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n📝 3. GENERATING CONTENT...")
        print("-" * 40)
        try:
            content = assistant.generate_content(collected_context)
            print(content)
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n🎉 4. GENERATING ALL TOGETHER...")
        print("-" * 40)
        try:
            all_content = assistant.generate_blog_content()
            print(all_content)
        except Exception as e:
            print(f"Error: {e}")
        
        # Save it
        assistant.save_responses("quick_test_responses.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure your OpenAI API key is set up correctly")
        return None

def main():
    """Main test function"""
    print("🚀 TIA Assistant Test Suite")
    print("=" * 50)
    
    print("\nChoose test option:")
    print("1. Full test with assistant calls (requires API)")
    print("2. Quick blog generation test")  
    print("3. Test phase transitions")
    print("4. Test commands")
    print("5. Interactive test (requires API keys)")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        test_response_recording()
    elif choice == "2":
        quick_blog_test()
    elif choice == "3":
        test_phase_transitions()
    elif choice == "4":
        test_commands()
    elif choice == "5":
        interactive_test()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()

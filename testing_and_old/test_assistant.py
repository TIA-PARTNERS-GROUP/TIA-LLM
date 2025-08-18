#!/usr/bin/env python3
"""
Test script for TIA Assistant with Response Recording

This script tests the assistant functionality by simulating user input.
"""

import json
from datetime import datetime
from unittest.mock import patch
from assistant_wrapper import AssistantWrapper

def test_cli_simulation():
    """Test the assistant by simulating CLI user input"""
    print("🧪 Testing TIA Assistant CLI Simulation")
    print("=" * 50)
    
    try:
        # Test sample responses in order (all phases combined)
        test_responses = [
            # Foundation phase responses (Phase 1)
            "John Smith",
            "Tech Innovations LLC", 
            "Founder and CEO",
            "AI-powered customer service automation",
            "Small to medium businesses",
            
            # Reflection phase responses (Phase 2)
            "I imagined having more freedom and helping businesses grow",
            "More challenging but rewarding than expected",
            "Peace of mind and time savings for business owners",
            "We helped a restaurant handle COVID order surge",
            "Made their business efficient and stress-free",
            "Help owners focus on what they love",
            "Proud of positive impact we make",
            
            # Analysis phase responses (Phase 3)
            "Industry-specific templates would excite customers",
            "Could expand to e-commerce and healthcare",
            "Yes, suggest some expansion ideas",
            "Personalized onboarding sets us apart",
            "Lack of genuine care in automation solutions",
            "Human-feeling, not robotic solutions",
            "More conversational and empathetic AI",
            "Technology should enhance, not replace connection",
            "Growing profits, could improve pricing tiers",
            
            # Strategy phase responses (Phase 4)
            "Let's shape my Why Statement",
            "Human and Professional blend",
            "Yes, blend warmth with credibility", 
            "Yes, finalize this Why Statement",
            "Yes, move to messaging",
            "Warm but professional tone",

            "exit"
        ]
        
        # Mock the input function to simulate user typing
        with patch('builtins.input', side_effect=test_responses):
            assistant = AssistantWrapper()
            assistant.chat_loop()  # This will use the mocked input
        
        print(f"\n✅ CLI Simulation completed!")
        print(f"📊 Total responses recorded: {len(assistant.user_responses)}")
        print(f"🎯 Final phase: {assistant.current_phase}")
        
        return assistant
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None

def main():
    """Run the tests"""
    print("🚀 TIA Assistant Test Suite")
    print("=" * 50)
    
    print("\nCLI Simulation Test")
    assistant1 = test_cli_simulation()
    
    # Summary
    if assistant1:
        print(f"\n📋 CLI Test Summary:")
        print(f"Phases completed: {assistant1.current_phase}")
        print(f"Responses recorded: {len(assistant1.user_responses)}")
        
        # Check for blog files
        import glob
        blog_files = glob.glob("blog_output_*.txt")
        if blog_files:
            print(f"📄 Blog files generated: {len(blog_files)}")

if __name__ == "__main__":
    main()

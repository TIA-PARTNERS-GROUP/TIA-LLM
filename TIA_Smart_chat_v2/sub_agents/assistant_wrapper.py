import os
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from prompts import (
    TIA_VISION_CHAT_1_FOUNDATION_PROMPT,
    TIA_VISION_CHAT_2_REFLECTION_PROMPT,
    TIA_VISION_CHAT_3_ANYLSIS_PROMPT,
    TIA_VISION_CHAT_4_STRATEGY_PROMPT,
    TIA_VISION_BLOG_1_WHY_STATEMENT_PROMPT,
    TIA_VISION_BLOG_2_MESSAGING_PROMPT,
    TIA_VISION_BLOG_3_CONTENT_PROMPT
)

MODEL = "gpt-4o"
BLOG_AMOUNT = 3
CHAT_PROMPTS = [
    TIA_VISION_CHAT_1_FOUNDATION_PROMPT,
    TIA_VISION_CHAT_2_REFLECTION_PROMPT, 
    TIA_VISION_CHAT_3_ANYLSIS_PROMPT,
    TIA_VISION_CHAT_4_STRATEGY_PROMPT
]

class AssistantWrapper:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.assistant_id = os.getenv('OPENAI_ASSISTANT_ID')
        
        if not self.assistant_id:
            raise ValueError("OPENAI_ASSISTANT_ID environment variable is required")
        
        self.conversation_history = []
        
        # Simple phase tracking
        self.current_phase = 1
        self.prompts = CHAT_PROMPTS
        
        # Record user responses
        self.user_responses = []
        self.system_prompt = self.prompts[0]  # Start with first prompt
    def send_message(self, message):
        """Send message using the modern Responses API and record user response"""
        # Record user response
        self.user_responses.append({
            'phase': self.current_phase,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
        self.conversation_history.append({
            "role": "user", 
            "content": message
        })
        
        input_messages = [
            {"role": "system", "content": self.system_prompt},
            *self.conversation_history
        ]
        
        response = self.client.responses.create(
            model=MODEL,
            input=input_messages
        )
        
        assistant_response = response.output_text
        self.conversation_history.append({
            "role": "assistant", 
            "content": assistant_response
        })
        
        return assistant_response
    
    def next_phase(self):
        """Move to next phase manually"""
        if self.current_phase < 4:
            self.current_phase += 1
            self.system_prompt = self.prompts[self.current_phase - 1]
            print(f"Moved to Phase {self.current_phase}")
        elif self.current_phase == 4:
            print("Generating blog content...")
            return self.generate_blog_content()
        return None
    
    def generate_blog_content(self):
        """Generate all blog content using the three separate prompts"""
        print("Generating Why Statement, Messaging, and Content...")
        
        # Format all responses into context
        collected_context = "\n".join([
            f"Phase {resp['phase']}: {resp['message']}" 
            for resp in self.user_responses
        ])
        
        results = []
        
        # 1. Generate Why Statement
        try:
            why_statement = self.generate_why_statement(collected_context)
            results.append("🎯 WHY STATEMENT:\n" + "="*50 + "\n" + why_statement + "\n")
        except Exception as e:
            results.append(f"❌ Error generating Why Statement: {e}\n")
        
        # 2. Generate Messaging
        try:
            messaging = self.generate_messaging(collected_context)
            results.append("📢 MESSAGING:\n" + "="*50 + "\n" + messaging + "\n")
        except Exception as e:
            results.append(f"❌ Error generating Messaging: {e}\n")
        
        # 3. Generate Content
        try:
            content = self.generate_content(collected_context)
            results.append("📝 CONTENT:\n" + "="*50 + "\n" + content + "\n")
        except Exception as e:
            results.append(f"❌ Error generating Content: {e}\n")
        
        return "\n".join(results)
    
    def generate_why_statement(self, collected_context):
        """Generate Why Statement using collected responses"""
        why_prompt = TIA_VISION_BLOG_1_WHY_STATEMENT_PROMPT.format(collected_context=collected_context)
        
        input_messages = [
            {"role": "system", "content": why_prompt}
        ]
        
        response = self.client.responses.create(
            model=MODEL,
            input=input_messages
        )
        
        return response.output_text
    
    def generate_messaging(self, collected_context):
        """Generate messaging (taglines, slogans, bios) using collected responses"""
        messaging_prompt = TIA_VISION_BLOG_2_MESSAGING_PROMPT.format(collected_context=collected_context)
        
        input_messages = [
            {"role": "system", "content": messaging_prompt}
        ]
        
        response = self.client.responses.create(
            model=MODEL,
            input=input_messages
        )
        
        return response.output_text
    
    def generate_content(self, collected_context):
        """Generate blog content and social captions using collected responses"""
        all_content = []
        
        for i in range(BLOG_AMOUNT):
            print(f"Generating content batch {i+1}/{BLOG_AMOUNT}...")
            
            content_prompt = TIA_VISION_BLOG_3_CONTENT_PROMPT.format(collected_context=collected_context)
            
            input_messages = [
                {"role": "system", "content": content_prompt}
            ]
            
            response = self.client.responses.create(
                model=MODEL,
                input=input_messages
            )
            
            all_content.append(f"\n{'='*20} CONTENT BATCH {i+1} {'='*20}\n{response.output_text}")
        
        return "\n".join(all_content)
    
    def save_responses(self, filename=None):
        """Save responses to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tia_responses_{timestamp}.json"
            
        with open(filename, 'w') as f:
            json.dump(self.user_responses, f, indent=2)
        print(f"Responses saved to {filename}")
        return filename
    
    def chat_loop(self):
        """Start an interactive chat session"""
        print("TIA Assistant Chat Session Started")
        print("Type 'quit', 'exit', or 'bye' to end")
        print("Type 'next' to go to next phase")
        print("Type 'save' to save responses")
        print("Type 'blog' to generate all blog content")
        print("Type 'why' to generate Why Statement only")
        print("Type 'messaging' to generate messaging only")
        print("Type 'content' to generate content only\n")
        
        try:
            while True:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("Goodbye!")
                    self.save_responses()
                    break
                    
                if user_input.lower() == 'next':
                    result = self.next_phase()
                    if result:
                        print(f"Blog Content:\n{result}")
                    continue
                    
                if user_input.lower() == 'save':
                    self.save_responses()
                    continue
                    
                if user_input.lower() == 'blog':
                    if len(self.user_responses) > 0:
                        blog_content = self.generate_blog_content()
                        print(f"Blog Content:\n{blog_content}")
                    else:
                        print("No responses recorded yet.")
                    continue
                
                if user_input.lower() == 'why':
                    if len(self.user_responses) > 0:
                        collected_context = "\n".join([f"Phase {resp['phase']}: {resp['message']}" for resp in self.user_responses])
                        why_statement = self.generate_why_statement(collected_context)
                        print(f"Why Statement:\n{why_statement}")
                    else:
                        print("No responses recorded yet.")
                    continue
                
                if user_input.lower() == 'messaging':
                    if len(self.user_responses) > 0:
                        collected_context = "\n".join([f"Phase {resp['phase']}: {resp['message']}" for resp in self.user_responses])
                        messaging = self.generate_messaging(collected_context)
                        print(f"Messaging:\n{messaging}")
                    else:
                        print("No responses recorded yet.")
                    continue
                
                if user_input.lower() == 'content':
                    if len(self.user_responses) > 0:
                        collected_context = "\n".join([f"Phase {resp['phase']}: {resp['message']}" for resp in self.user_responses])
                        content = self.generate_content(collected_context)
                        print(f"Content:\n{content}")
                    else:
                        print("No responses recorded yet.")
                    continue
                
                if not user_input:
                    continue
                
                print("Assistant is thinking...")
                try:
                    response = self.send_message(user_input)
                    print(f"Assistant: {response}\n")
                except Exception as e:
                    print(f"Error: {e}\n")
        
        except KeyboardInterrupt:
            print("\nChat session ended.")
            self.save_responses()

# Testing in file
if __name__ == "__main__":
    """Main function to run the assistant"""
    try:
        assistant = AssistantWrapper()
        assistant.chat_loop()
    except Exception as e:
        print(f"Error: {e}")
        print("Please make sure OPENAI_API_KEY and OPENAI_ASSISTANT_ID are set in your .env file.")
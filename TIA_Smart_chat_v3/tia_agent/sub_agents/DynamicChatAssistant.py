from datetime import datetime
from litellm import completion
from ..config import CHAT_MODEL, OPENAI_API_KEY
import re, logging, json, os

logger = logging.getLogger(__name__)

# Function to generate response using LiteLLM
def generate_response(message):
    response = completion(
        model=CHAT_MODEL,
        messages=message,
        api_key=OPENAI_API_KEY
    )
    return response.choices[0].message.content.strip()

class DynamicChatAssistant:
    """
    Manages multi-phase conversations using predefined prompts and rules.
    Guides users through phases, collects responses, and resets history per phase.
    Transitions based on user input and rules.

    Attributes:
        user_id (int): ID of the user.
        current_phase (int): Current phase index.
        prompts (list): List of chat prompts for each phase.
        rule_prompt (str): Template for wrapping chat prompts with rules.
        conversation_history (list): History of messages in the current phase.
        user_responses (list): Collected user responses across phases.
        system_prompt (str): Current system prompt based on phase.
        assistant_response (str): Latest response from the assistant.
        business_info (dict): Information about the user's business.
        end_chat_session (bool): Flag indicating if the chat session has ended.
    """
    def __init__(self, prompts: list, rule_prompt: str, user_id: int):
        logger.info(f"Initializing DynamicChatAssistant for user_id: {user_id}")
        self.user_id = user_id
        self.current_phase = 0
        self.prompts = prompts
        self.rule_prompt = rule_prompt
        self.conversation_history = []
        self.user_responses = []
        self.system_prompt = self._get_wrapped_prompt(0)
        self.assistant_response = ""
        self.business_info = {}
        self.end_chat_session = False
        
    def _get_wrapped_prompt(self, phase_index):
        """Wrap the chat prompt with the connect rule prompts"""
        chat_prompt = self.prompts[phase_index]
        return self.rule_prompt.format(chat_prompt=chat_prompt)

    def _next_phase(self):
        """Move to next phase - generate partner matches"""
        max_phase = len(self.prompts) - 1
        if self.current_phase < max_phase:
            self.current_phase += 1
            self.system_prompt = self._get_wrapped_prompt(self.current_phase)
            self.conversation_history.clear()
            logger.info(f"DynamicChat for user_id: {self.user_id} - [Moved to Phase {self.current_phase} / {max_phase}] - Conversation history cleared")
            return None
        if self.current_phase == max_phase:
            self.conversation_history.clear()
            #self.save_responses() # Save responses for infile testing
            self.end_chat_session = True
            return "<exit>"

    def send_message(self, message):
        """Send message using litellm with chosen API and record user response"""
        logger.debug(f"DynamicChatAssistant user_id: {self.user_id} - [On Phase {self.current_phase} / {len(self.prompts) - 1}] - Sending message")
        self.user_responses.append({
            'phase': self.current_phase,
            'question': self.assistant_response,
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

        # logger.debug("=" * 20)
        # logger.debug(f"*self.conversation_history: {self.conversation_history}")
        # logger.debug("=" * 20)

        self.assistant_response = generate_response(input_messages)

        self.conversation_history.append({
            "role": "assistant", 
            "content": self.assistant_response
        })

        # Check if the response contains the end tag if there is one go to the next phase
        end_tag = r'<\s*END_OF_TIA_PROMPT\s*>'
        if re.search(end_tag, self.assistant_response):
            self.assistant_response = re.sub(end_tag, '', self.assistant_response).strip()
            self.conversation_history[-1]["content"] = self.assistant_response
            next_phase_result = self._next_phase()
            if next_phase_result:
                return self.assistant_response + "\n\n" + next_phase_result
            else:
                # Automatically generate the first assistant message for the new phase
                fresh_phase_message = f"**Start with a very short message indicating we will continue to the next phase. Keep it brief and conversational.** \n\n{self.system_prompt}"
                first_input_messages = [{"role": "system", "content": fresh_phase_message}]
                self.assistant_response = generate_response(first_input_messages)
                self.conversation_history.append({
                    "role": "assistant", 
                    "content": self.assistant_response
                })
                return self.assistant_response
        
        return self.assistant_response

    # NOTE: Only used for infile testing currently
    def save_responses(self):
        """Save responses to JSON file"""
        if self.user_id is None:
            search_string = "UNKNOWN_USER__DATE-" + datetime.now().strftime("%Y%m%d_%H%M%S")
        else:
            search_string = f"{self.user_id}__DATE-" + datetime.now().strftime("%Y%m%d_%H%M%S")
        # Get the parent directory of the current file
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        temp_dir = os.path.join(parent_dir, "tmp/sub_agent_chat_history")
        os.makedirs(temp_dir, exist_ok=True)
        filename = os.path.join(temp_dir, f"tia_responses_{search_string}.json")

        with open(filename, 'w') as f:
            json.dump(self.user_responses, f, indent=2)
        logger.debug(f"Responses saved to {filename}")
        return filename
    
    # def collect_user_history(self):
    #     """Find the user's most recent conversation history from tia_responses_{user_id}__DATE-*.json files under temp"""
    #     try:
    #         # Use the same temp_dir path as in the class
    #         parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    #         temp_dir = os.path.join(parent_dir, "tmp", "sub_agent_chat_history")
    #         user_id = self.user_id or "UNKNOWN_USER"
    #         pattern = rf"tia_responses_{user_id}__DATE-(\d{{8}}_\d{{6}})\.json"
    #         latest_file = None
    #         latest_dt = None

    #         for fname in os.listdir(temp_dir):
    #             match = re.match(pattern, fname)
    #             if match:
    #                 dt_str = match.group(1)
    #                 dt = datetime.strptime(dt_str, "%Y%m%d_%H%M%S")
    #                 if latest_dt is None or dt > latest_dt:
    #                     latest_dt = dt
    #                     latest_file = fname

    #         # NOTE: THIS WAS FOR POTENTIAL HISTORY LOADING, CURRENTLY NOT IN USE AS SAVE RESPONCES IS DISABLED
    #         if latest_file is None:
    #             logger.debug("No conversation history found.")
    #             return None
    #         filename = os.path.join(temp_dir, latest_file)
    #         with open(filename, 'r') as f:
    #             user_history = json.load(f)
    #         return user_history
    #     except Exception as e:
    #         logger.debug(f"Error collecting user history: {e}")
    #         return None

# TESTING CODE FOR STANDALONE RUNNING
if __name__ == "__main__":
    DYNAMIC_CHAT_RULE_PROMPT = """
    You are TIA Vision — a warm, conversational assistant helping entrepreneurs uncover the heart of their brand.

    When you reach the final numbered question you must include a marked tag of `<END_OF_TIA_PROMPT>` to indicate the end of the current phase.

    Follow the exact sequence of questions below:
    {chat_prompt}

    This tag MUST appear at the end of your response after the user answers the last question. Do not skip this step.

    🗣️ GLOBAL INSTRUCTIONS:

    - Ask **one question per turn** unless the prompt explicitly allows more.
    - After each answer, **briefly reflect back** what you heard to build rapport.
    - **Do NOT** move to the next question until the current one is answered.
    - Don't include numbers in your responses keep it conversational.
    - Keep responses warm and conversational.
    """


    TIA_VISION_CHAT_1_FOUNDATION_PROMPT = """
    Your task is to guide the user through Steps 0 to 4 using friendly, clear language. Ask one question at a time. After each response, reflect briefly and transition smoothly to the next step.

    🎯 Goals:
    - Capture the user's personal identity and their business fundamentals.
    - Make them feel seen, heard, and understood.
    - Create a foundation that future steps can build upon (e.g., their Why, tone, messaging).

    🧠 Use this context when responding:
    - Tone: Conversational, human, supportive
    - Audience: Startup founder or small business owner
    - Purpose: Help them articulate what they do and who they serve in simple, authentic terms
    
    🪜 Steps to ask (in order):
    1. "Let's start with the basics, a bit about the business?"
    2. "What is your role in the company?"
    3. "What kind of product or service do you offer?"
    4. "Who is your typical customer or client?"
    """

    TIA_VISION_CHAT_2_REFLECTION_PROMPT = """
    This section is about going deeper. Help the user reflect on their personal motivations, emotional connection to the business, and the human impact they want to create.

    🎯 Goals:
    - Uncover the emotional roots of their business journey
    - Help them connect their work to real people, stories, and outcomes
    - Capture the deeper "why" behind their brand's existence
    - Lay the groundwork for crafting a strong, personal Why Statement later

    🧠 Tone & Style:
    - Human, curious, and empathetic
    - Encourage storytelling and honest reflection
    - Make them feel safe to open up — like a mentor or close friend

    🪜 Steps to ask (in order), one at a time:
    1. "When you first started your business, what did you imagine life would look like?"
    2. "How do you feel about your business now compared to back then?"
    3. "What does your product or service do for the end user in human terms?"
    4. "Can you recall a time your business made a difference to someone?"
    5. "Imagine your ideal client – what would you love them to say about your service after working with you?"
    6. "What's the deeper impact of your work for others?"
    7. "How would you like your team to feel about their work?"
    """

    prompts = [
        TIA_VISION_CHAT_1_FOUNDATION_PROMPT,
        TIA_VISION_CHAT_2_REFLECTION_PROMPT
    ]

    assistant = DynamicChatAssistant(
        prompts=prompts,
        rule_prompt=DYNAMIC_CHAT_RULE_PROMPT,
        user_id=123
    )

    print("=== TIA Vision Chat Assistant ===")
    print("Welcome! I'm TIA Vision, here to help you uncover the heart of your brand.")
    print("We'll go through 2 phases:")
    print("Phase 1: Foundation - Understanding your business basics")
    print("Phase 2: Reflection - Exploring your deeper motivations")
    print("\nType 'quit', 'exit', or 'q' to end anytime")
    print("Type 'status' to see your progress")
    print("Type 'history' to see your responses")
    print("-" * 50)
    
    # Start the conversation
    print(f"\n🎯 Phase {assistant.current_phase + 1}/2: Foundation")
    print("TIA Vision: Let's start with the basics - tell me a bit about your business?")
    
    while True:
        try:
            if assistant.end_chat_session:
                print("\n" + "=" * 50)
                print("Congratulations! You've completed both phases!")
                print("Your responses have been saved for blog generation.")
                print("This data can now be used to create your Why Statement and messaging!")
                print("=" * 50)
                break
            
            user_input = input(f"\nYou [Phase {assistant.current_phase + 1}/2]: ").strip()
            
            # Handle commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nThanks for using TIA Vision!")
                if assistant.user_responses:
                    save_choice = input("Save your progress? (y/n): ").strip().lower()
                    if save_choice == 'y':
                        filename = assistant.save_responses()
                        print(f"Saved to: {filename}")
                break
                
            elif user_input.lower() == 'status':
                phase_names = ["Foundation", "Reflection"]
                current_name = phase_names[assistant.current_phase]
                print(f"\nStatus:")
                print(f"   Phase: {assistant.current_phase + 1}/2 ({current_name})")
                print(f"   Questions answered: {len(assistant.user_responses)}")
                continue
                
            elif user_input.lower() == 'history':
                print(f"\nYour responses:")
                if not assistant.user_responses:
                    print("   No responses yet.")
                else:
                    for i, resp in enumerate(assistant.user_responses):
                        phase_name = "Foundation" if resp['phase'] == 0 else "Reflection"
                        print(f"   {i+1}. [{phase_name}] {resp['message'][:60]}...")
                continue
                
            elif not user_input:
                print("Please enter a response or command.")
                continue
            
            # Send message
            print("\nTIA Vision is thinking...")
            response = assistant.send_message(user_input)
            print(f"\nTIA Vision: {response}")
            
            # Check for phase transition
            if "Phase 2" in response or "Reflection" in response:
                print(f"\nPhase {assistant.current_phase + 1}/2: Reflection")
            
            print("-" * 40)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again or type 'quit' to exit.")
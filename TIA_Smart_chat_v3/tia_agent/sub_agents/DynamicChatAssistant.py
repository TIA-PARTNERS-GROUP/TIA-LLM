from datetime import datetime
from litellm import completion
from ..config import CHAT_MODEL, OPENAI_API_KEY
import re, logging, json, os

def generate_response(message):
    response = completion(
        model=CHAT_MODEL,
        messages=message,
        api_key=OPENAI_API_KEY
    )
    return response.choices[0].message.content.strip()

class DynamicChatAssistant:
    def __init__(self, prompts: list, rule_prompt: str, user_id: int):
        # Phase tracking, user history and responses
        self.user_id = user_id
        self.current_phase = 0
        self.prompts = prompts
        self.rule_prompt = rule_prompt
        self.conversation_history = []
        self.user_responses = []
        self.system_prompt = self._get_wrapped_prompt(0)
        self.assistant_response = "" # Set first reply to empty string
        self.business_info = {}
        self.end_chat_session = False

        # Log file setup
        log_file = f"conversation_connect_chat_history.log"

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
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
            print()
            print(f"[Moved to Phase {self.current_phase}] - Conversation history cleared")
            return None
        if self.current_phase == max_phase:
            self.conversation_history.clear()
            self.save_responses()
            self.end_chat_session = True
            return "<exit>"

    def send_message(self, message):
        """Send message using litellm with chosen API and record user response"""
        # Record user response
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

        self.logger.info("=" * 20)
        self.logger.info(f"*self.conversation_history: {self.conversation_history}")
        self.logger.info("=" * 20)

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
        
        return self.assistant_response

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
        print(f"Responses saved to {filename}")
        return filename
    
    def collect_user_history(self):
        """Find the user's most recent conversation history from tia_responses_{user_id}__DATE-*.json files under temp"""
        try:
            # Use the same temp_dir path as in the class
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            temp_dir = os.path.join(parent_dir, "tmp", "sub_agent_chat_history")
            user_id = self.user_id or "UNKNOWN_USER"
            pattern = rf"tia_responses_{user_id}__DATE-(\d{{8}}_\d{{6}})\.json"
            latest_file = None
            latest_dt = None

            for fname in os.listdir(temp_dir):
                match = re.match(pattern, fname)
                if match:
                    dt_str = match.group(1)
                    dt = datetime.strptime(dt_str, "%Y%m%d_%H%M%S")
                    if latest_dt is None or dt > latest_dt:
                        latest_dt = dt
                        latest_file = fname

            if latest_file is None:
                self.logger.info("No conversation history found.")
                return None
            filename = os.path.join(temp_dir, latest_file)
            with open(filename, 'r') as f:
                user_history = json.load(f)
            return user_history
        except Exception as e:
            self.logger.error(f"Error collecting user history: {e}")
            return None
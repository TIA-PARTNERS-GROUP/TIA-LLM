from google.adk.agents import Agent
from .config import model
from .sub_agents.question_agent import question_agent
from .sub_agents.question_checker_agent import question_checker_agent
from .sub_agents.general_chat_agent import general_chat_agent

coordinatorAgent = Agent(
    name="CoordinatorAgent",
    model=model,
    description="Manages the TIA Vision conversation flow, routing between question asking, validation, and off-topic redirection.",
    sub_agents=[question_agent, question_checker_agent, general_chat_agent],
    instruction="""
    You coordinate the TIA Vision chat flow using sub-agents and the CSV-based step sequence.

    ## 🌱 1. Conversation Start:
    - Always begin by calling `GeneralChatAgent`.
    - If the shared state has no `tia_question` or `tia_current_step`, this is the first time the user is interacting.
      → In this case, `GeneralChatAgent` should greet the user and explain that this chat will guide them through a structured set of questions to understand their business and goals.
    - Once the user indicates they're ready to begin, call `QuestionAgent` with `user_response=""`.

    ## 🔁 2. Question Loop (Step-by-Step):
    After each user message:
    1. Call `QuestionCheckerAgent`.
       - It compares the user's message to:
         - The current `question` (`tia_question`)
         - The expected answer (`tia_current_expectation`)
       - It will return **"True"** or **"False"**.

    2. Based on the result:
       - If `"True"`:
         - Save the user's message in state as `tia_user_response`.
         - Call `QuestionAgent` with that response to move to the next step in the CSV.
       - If `"False"`:
         - Call `GeneralChatAgent`:
           - It will acknowledge the unrelated message.
           - Then restate the current `tia_question` from state.
         - Then wait for the next user response and repeat step 1.

    ## 🧭 When to Use `GeneralChatAgent`:
    - At the **beginning** when no step/question is active (no `tia_question` in state) → greet and explain purpose.
    - At **any point** where a response is off-topic (i.e., `QuestionCheckerAgent` returns `"False"`) → redirect gently to the current question.

    ## ✅ 3. Completion:
    - When `tia_flow_complete = True` (i.e., all 31 steps are complete), stop all agents.
    - Return the final thank-you message from `QuestionAgent`.

    ## 🚫 Do NOT:
    - Generate replies or questions yourself.
    - Validate responses manually.
    - Skip agent calls or flow steps.
    """
)
  
root_agent = coordinatorAgent
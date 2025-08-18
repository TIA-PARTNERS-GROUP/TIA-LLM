from google.adk.agents import Agent
from ..TIA_Smart_chat.tools.get_next_question import get_next_question
from google.adk.models.lite_llm import LiteLlm
import os
from google.adk.agents import Agent, LlmAgent, BaseAgent, SequentialAgent, LoopAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from typing import AsyncGenerator

os.environ["OPENAI_API_KEY"] = "unused"
os.environ["OPENAI_API_BASE"] = "http://localhost:11434/v1"

#OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_MODEL = "qwen3:14b"
#OLLAMA_MODEL = "qwen3:8b"
MAX_STEP = 31
model = LiteLlm(model=f"openai/{OLLAMA_MODEL}")

question_checker_agent = Agent(
    name="QuestionCheckerAgent",
    model=model,
    description="Checks if user response matches the expected answer type.",
    instruction="""
    You check if the user's response is relevant to the current question.

    Use shared state:
    - `question`: the current question
    - `expecting_next`: the expected answer type

    Compare these to `user_response`. Doesn't have to be exact user can be analysis to see if it answers the asked `question`, use `expecting_next` as a sudo guide. Focus on whether the user's response meaningfully addresses the question, even if the answer is embedded within their context.

    If the response matches the expectation → reply: ✅ That makes sense.  
    If not → reply only with: not related

    Do not call tools or ask follow-up questions.
    """
)

chat_agent = Agent(
    name="TIAVisionAgent",
    model=model,
    tools=[get_next_question],
    description="Guides the user through the TIA Vision flow using the `get_next_question` tool.",
    instruction="""
You guide the user through the TIA Vision flow, one question at a time, using the `get_next_question` tool.

---

## 🔹 Tool Usage: `get_next_question`

- You MUST call this tool to retrieve each new step in the flow.
- To start: call with `user_response=""`.
- For each reply: call with the actual user input as `user_response`.

---

## 🗣️ How to Ask the Question:

- Use the `question` field from the tool output as a **semantic guide**, not a script.
- Structure a clear, professional, and friendly prompt based on the meaning of the question.
- You may rewrite the wording to improve clarity, make it more engaging, or sound natural — but **you must not alter the intent**.
- You MUST NOT invent any new questions, content, or steps not provided by the tool.

**Examples:**

If the tool returns:
```json
{ "question": "What is your role in the TIA Vision process?" }
You could ask:

To help tailor the next steps, could you briefly describe your role in the TIA Vision process?

✅ This rewording is valid because it:

Matches the meaning

Adds clarity and friendliness

Does not introduce new information

📌 Rules
Always use the get_next_question tool before responding.

Always base your question on the tool's output — never make one up.

Do not validate user responses. That is handled by another agent.

Do not continue unless the tool response is successful.

When the tool indicates "status": "done", end the flow and show the message.

"""
)

restate_agent = Agent(
    name="RestateAgent",
    model=model,
    description="Restates the current question and prompts user to answer it again.",
    instruction="""
    Repeat the last question from shared state (`tia_question`) and ask the user to try again.

    - Do not guess what the user meant.
    - Do not explain.
    - Simply repeat the question and kindly ask for a better or clearer answer.
    """
    )

coordinatorAgent = Agent(
    name="CoordinatorAgent",
    model=model,
    description="Coordinates the TIA Vision flow by routing between asking questions and validating user responses.",
    sub_agents=[chat_agent, question_checker_agent, restate_agent],
    instruction="""
    You coordinate the TIA Vision flow by calling sub-agents in order.

    Start by greeting the user, explaing you are a TIA Smart Connect Chat Bot, your goal is to help guide the user through questions to better understand them and find matching business partners for them.

    ---

    ## 🔁 Sequence Control:

    1. Start the flow by calling `TIAVisionAgent` with an empty `user_response`.
    2. Wait for the user to answer.
    3. Call `QuestionCheckerAgent` to validate the user's response.
    4. Either Move onto the next question (repeat sequence, go to step 1) if the response it valid or call `RestateAgent` and got to step 2 after

    ---

    ## ✅ If the response is valid:
    - Store the user's input in shared state as `tia_user_response`.
    - Call `TIAVisionAgent` again with the new response to proceed to the next question.

    ## ❌ If invalid:
    - Call `RestateAgent` which will restate the same question again with a polite tone.
    - Then continue from step 2

    ---

    ## 🛑 Ending the Flow:
    - When `TIAVisionAgent` sets `tia_flow_complete = True`, stop calling agents and return the final message.

    ---

    📌 You must:
    - Control the sequence of agents.
    - Route tool calls and validation responses using shared state.
    - Yield to user input where appropriate.

    📌 You must NOT:
    - Generate your own messages.
    - Validate answers yourself.
    - Skip any required steps.
    """
)
    
root_agent = coordinatorAgent

#root_agent = chat_agent
# import pandas as pd

# csv_file = "/home/joshua/tia_connect/TIA_Smart_chat/chat_flow.csv"
# CHAT_FLOW = pd.read_csv(csv_file)
# TIA_FLOW = CHAT_FLOW[CHAT_FLOW["chat_area"] == "tia_vision"].reset_index(drop=True)

# # ROUTER
# class TIAConnect(BaseAgent):
#     """
#     Custom orchestrator for TIA Smart Connect Chat.
#     Routes user input to either the chat agent (structured flow) or tool agents.
#     Manages the QuestionCheckerAgent flow.
#     """

#     question_checker_agent: Agent
#     chat_agent: Agent
#     restate_agent: Agent

#     model_config = {"arbitrary_types_allowed": True}

#     def __init__(self, name: str, question_checker_agent: Agent, chat_agent: Agent, restate_agent: Agent):
#         sub_agents_list = [
#             question_checker_agent,
#             chat_agent,
#             restate_agent
#         ]
#         super().__init__(
#             name=name,
#             question_checker_agent=question_checker_agent,
#             chat_agent=chat_agent,
#             restate_agent=restate_agent,
#             sub_agents=sub_agents_list,
#         )

#     def extract_text(self, event: Event) -> str:
#         if event.content and event.content.parts:
#             for part in event.content.parts:
#                 if hasattr(part, "text") and part.text:
#                     return part.text.strip()
#         return ""


#     async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
#         """
#         One loop step:
#         - If first step, run chat_agent to start.
#         - Then check user input with question_checker_agent.
#         - If valid, continue with chat_agent to ask next question.
#         """

#         state = ctx.session.state
#         step = state.get("tia_current_step", -1)

#         print("[DEBUG] Step:", step)
#         print("[DEBUG] Current Question:", state.get("tia_question"))
#         print("[DEBUG] Expectation:", state.get("tia_current_expectation"))
#         print("[DEBUG] Checker Rejected:", state.get("checker_rejected"))

#         if step < 0:
#             print("[DEBUG] Starting TIA Vision flow")
#             async for event in self.chat_agent.run_async(ctx):
#                 yield event
#             state["tia_current_step"] = 0
#             return

#         async for event in self.question_checker_agent.run_async(ctx):
#             yield event

#         text = self.extract_text(event)
#         if "not related" in text.lower():
#             print("[DEBUG] THIS SHIT UNRELATED")
#             async for event in self.restate_agent.run_async(ctx):
#                 yield event
#             return

#         # JOSHUA - TOOL SHOULD HANDLE THIS DECIDE
#         next_step = step + 1
#         if next_step < len(TIA_FLOW):
#             async for event in self.chat_agent.run_async(ctx):
#                 yield event
#             return

# REWORK get_next_question tool
# HIDE THOUGHT PROCESSING USE .final_responce
# EXPOSED AGENT
# root_agent = TIAConnect(
#     name="RAGAgent",
#     question_checker_agent=question_checker_agent,
#     chat_agent=chat_agent,
#     restate_agent=restate_agent,
# )

# chat_agent = Agent(
#     name="TIAVisionAgent",
#     model=model,
#     tools=[get_next_question],
#     description="Guides the user through the TIA Vision flow using the `get_next_question` tool.",
#     instruction="""
# You guide the user through the TIA Vision flow, one question at a time, using the `get_next_question` tool.

# ---

# ## 🔹 Tool Usage: `get_next_question`

# - You MUST call this tool to retrieve each new step in the flow.
# - To start: call with `user_response=""`.
# - For each reply: call with the actual user input as `user_response`.

# ---

# ## 🗣️ How to Ask the Question:

# - Use the `question` field from the tool output as a **semantic guide**, not a script.
# - Structure a clear, professional, and friendly prompt based on the meaning of the question.
# - You may rewrite the wording to improve clarity, make it more engaging, or sound natural — but **you must not alter the intent**.
# - You MUST NOT invent any new questions, content, or steps not provided by the tool.

# **Examples:**

# If the tool returns:
# ```json
# { "question": "What is your role in the TIA Vision process?" }
# You could ask:

# To help tailor the next steps, could you briefly describe your role in the TIA Vision process?

# ✅ This rewording is valid because it:

# Matches the meaning

# Adds clarity and friendliness

# Does not introduce new information

# 📌 Rules
# Always use the get_next_question tool before responding.

# Always base your question on the tool's output — never make one up.

# Do not validate user responses. That is handled by another agent.

# Do not continue unless the tool response is successful.

# When the tool indicates "status": "done", end the flow and show the message.

# """
# )
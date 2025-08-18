# from google.adk.agents import Agent
# from .tools.get_next_question import get_next_question
# from google.adk.models.lite_llm import LiteLlm
# import os
# from google.adk.agents import Agent, LlmAgent, BaseAgent, SequentialAgent, LoopAgent
# from google.adk.agents.invocation_context import InvocationContext
# from google.adk.events import Event, EventActions
# from typing import AsyncGenerator
# from pydantic import BaseModel, Field
# import json

# os.environ["OPENAI_API_KEY"] = "unused"
# os.environ["OPENAI_API_BASE"] = "http://localhost:11434/v1"

# #OLLAMA_MODEL = "qwen2.5:7b"
# OLLAMA_MODEL = "qwen3:14b"
# #OLLAMA_MODEL = "qwen3:8b"
# MAX_STEP = 31
# model = LiteLlm(model=f"openai/{OLLAMA_MODEL}")

# question_checker_agent = Agent(
#     name="QuestionCheckerAgent",
#     model=model,
#     description="Checks if user response matches the expected answer type.",
#     instruction="""
#     You check if the user's response is relevant to the current question.

#     Use shared state:
#     - `question`: the current question
#     - `expecting_next`: the expected answer type

#     Compare these to `user_response`. Doesn't have to be exact user can be analysis to see if it answers the asked `question`, use `expecting_next` as a sudo guide. Focus on whether the user's response meaningfully addresses the question, even if the answer is embedded within their context.

#     If the response matches the expectation → reply: True.  
#     If not → reply only with: False

#     Do not call tools or ask follow-up questions.
#     """,
#     output_key="Relevant"
# )

# chat_agent = Agent(
#     name="TIAVisionAgent",
#     model=model,
#     tools=[get_next_question],
#     description="Guides the user through the TIA Vision flow using the `get_next_question` tool.",
#     instruction="""
#     You guide the user through the TIA Vision flow, one question at a time, using the `get_next_question` tool.

#     ---

#     ## 🔹 Tool Usage: `get_next_question`

#     - You MUST call this tool to retrieve each new step in the flow.
#     - To start: call with `user_response=""`.
#     - For each reply: call with the actual user input as `user_response`.

#     ---

#     ## 🗣️ How to Ask the Question:

#     - Use the `question` field from the tool output as a **semantic guide**, not a script.
#     - Structure a clear, professional, and friendly prompt based on the meaning of the question.
#     - You may rewrite the wording to improve clarity, make it more engaging, or sound natural — but **you must not alter the intent**.
#     - You MUST NOT invent any new questions, content, or steps not provided by the tool.

#     **Examples:**

#     If the tool returns:
#     ```json
#     { "question": "What is your role in the TIA Vision process?" }
#     You could ask:

#     To help tailor the next steps, could you briefly describe your role in the TIA Vision process?

#     ✅ This rewording is valid because it:

#     Matches the meaning

#     Adds clarity and friendliness

#     Does not introduce new information

#     📌 Rules
#     Always use the get_next_question tool before responding.

#     Always base your question on the tool's output — never make one up.

#     Do not validate user responses. That is handled by another agent.

#     Do not continue unless the tool response is successful.

#     When the tool indicates "status": "done", end the flow and show the message.

#     """
# )

# restate_agent = Agent(
#     name="RestateAgent",
#     model=model,
#     description="Restates the current question and prompts user to answer it again.",
#     instruction="""
#     Repeat the last question from shared state (`tia_question`) and ask the user to try again.

#     - Do not guess what the user meant.
#     - Do not explain.
#     - Simply repeat the question and kindly ask for a better or clearer answer.
#     """
#     )

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
#     start_agent: Agent

#     model_config = {"arbitrary_types_allowed": True}

#     def __init__(self, name: str, start_agent: Agent, question_checker_agent: Agent, chat_agent: Agent, restate_agent: Agent):
#         sub_agents_list = [
#             question_checker_agent,
#             chat_agent,
#             restate_agent,
#         ]
#         super().__init__(
#             name=name,
#             start_agent=start_agent,
#             question_checker_agent=question_checker_agent,
#             chat_agent=chat_agent,
#             restate_agent=restate_agent,
#             sub_agents=sub_agents_list,
#         )

#     def extract_text(self, event: Event) -> bool:
#         if event.content and event.content.parts:
#             for part in event.content.parts:
#                 if hasattr(part, "text"):
#                     try:
#                         data = part.text if isinstance(part.text, dict) else json.loads(part.text)
#                         if "Relevant" in data:
#                             return bool(data["Relevant"])
#                     except Exception:
#                         pass
#         return False


#     async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
#         """
#         One loop step:
#         - If first step, run chat_agent to start.
#         - Then check user input with question_checker_agent.
#         - If valid, continue with chat_agent to ask next question.
#         """
#         state = ctx.session.state
#         step = state.get("tia_current_step", -1)
#         print("[DEBUG] Step:", state.get("begin_requested") )


#         if state.get("begin_requested") == True:
#             print("[DEBUG] Step:", step)
#             print("[DEBUG] Current Question:", state.get("question"))
#             print("[DEBUG] Expectation:", state.get("expecting_next"))

#             async for event in self.chat_agent.run_async(ctx):
#                 yield event

#             async for event in self.question_checker_agent.run_async(ctx):
#                 yield event

#             relevant = self.extract_text(event)
#             if not relevant:
#                 print("[DEBUG] THIS SHIT UNRELATED")
#                 async for event in self.restate_agent.run_async(ctx):
#                     yield event
#             else:
#                 ctx.session.state.update(event)
#         else:
#             async for event in self.start_agent.run_async(ctx):
#                 yield event
#             return

# start_agent = Agent(
#     name="StartAgent",
#     model=model,
#     description="Introduces the TIA Smart Connect Chat and waits for the user to say 'Begin' to proceed.",
#     instruction="""
#     You are the starting agent for the TIA Smart Connect Chat.

#     ---

#     🔹 Purpose:
#     Introduce yourself to the user as the TIA Smart Connect Assistant.
#     Explain that your job is to guide them through a short series of questions to help match them with the right business partners.

#     ---

#     🔹 Your Task:
#     1. Politely greet the user and describe what this chat is for.
#     2. Ask them to say **"Begin"** to start the process.
#     3. Wait for their input.
#     4. If the user’s response includes the word **begin** (case-insensitive), reply with:
#     ✅ Understood. Let's get started.
#     Then set the output key `begin_requested = True`.

#     If they say anything else:
#     - Politely remind them to type **"Begin"** to proceed.
#     - Do not move on until they do.

#     ---

#     📌 Rules:
#     - Only check for the word "begin" (case-insensitive) in the user's input.
#     - Do not invent questions or steps.
#     - Do not call any tools.
#     - Only proceed when `begin_requested` is set to True.
#     """,
#     output_key="begin_requested"
# )
        
# root_agent = TIAConnect(
#     name="ControlAgent",
#     start_agent=start_agent,
#     question_checker_agent=question_checker_agent,
#     chat_agent=chat_agent,
#     restate_agent=restate_agent,
# )


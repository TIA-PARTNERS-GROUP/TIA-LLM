import pandas as pd
from google.adk.tools.tool_context import ToolContext
from google.adk.agents import Agent, SequentialAgent
from ..config import model

# Load the TIA Vision flow once
csv_file = "/home/joshua/tia_connect/TIA_Smart_chat/chat_flow.csv"
CHAT_FLOW = pd.read_csv(csv_file)
TIA_FLOW = CHAT_FLOW[CHAT_FLOW["chat_area"] == "tia_vision"].reset_index(drop=True)


def get_next_question(user_response: str, tool_context: ToolContext) -> dict:
    state = tool_context.state
    step = state.get("tia_current_step", 0)
    responses = state.get("tia_responses", {})
    expectations = state.get("tia_expectations", {})

    # Save last answer only if user_response is provided
    if step > 0 and user_response:
        responses[str(step - 1)] = user_response
        expectations[str(step - 1)] = state.get("tia_current_expectation", "")

    if step >= len(TIA_FLOW):
        return {
            "status": "done",
            "message": "TIA Vision flow complete. Thank you!",
            "responses": responses,
            "expectations": expectations,
        }

    row = TIA_FLOW.iloc[step]
    question = row["desired_questions"]
    expectation = row["desired_answers"]

    state["tia_current_step"] = step + 1
    state["tia_responses"] = responses
    state["tia_expectations"] = expectations
    state["tia_current_expectation"] = expectation

    return {
        "status": "success",
        "question": question,
        "expecting_next": expectation,
        "step": step,
    }

get_next_question_agent = Agent(
    name="GetNextQuestionAgent",
    model=model,
    tools=[get_next_question],
    description="Calls the `get_next_question` tool and stores the result in state.",
    instruction="""
    Your only task is to call the `get_next_question` tool.

    - If this is the first step, call it with `user_response=""`.
    - Otherwise, call it with the user's most recent reply.

    Do not say anything. Do not generate a message. Just call the tool and update state.
    """
)

present_question_agent = Agent(
    name="PresentQuestionAgent",
    model=model,
    description="Reads the latest tool output from state and asks the user the next question.",
    instruction="""
    You are presenting the next question in the TIA Vision flow.

    Use the following context from shared state:

    <tia_context>
    Step: {tia_current_step}
    Prior Answers: {tia_responses}
    Expected Type: {tia_current_expectation}
    </tia_context>

    ---

    Your task:
    - Use the question retrieved from the last tool call (stored as `question`)
    - Phrase it clearly and professionally
    - Add friendliness if appropriate
    - Do not change the intent
    - You are to use the questions 

    ✅ Example:
    If the question is: "What is your role?"  
    You can say: "Could you please describe your role so I can better understand you as a worker and person?"

    📌 Rules:
    - Do not call tools
    - Do not invent new questions
    - Do not validate answers
    - If `tia_flow_complete = True`, say a polite thank you and stop
    """
)

question_agent = SequentialAgent(
    name="QuestionAgent",
    description="Handles both the tool call and question presentation for the TIA Vision flow.",
    sub_agents=[get_next_question_agent, present_question_agent],
)
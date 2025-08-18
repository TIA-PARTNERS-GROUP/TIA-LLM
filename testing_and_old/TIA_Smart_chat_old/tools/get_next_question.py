"""
Tool for guiding the TIA Vision structured conversation flow using chat_flow.csv.
"""

import pandas as pd
from google.adk.tools.tool_context import ToolContext

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


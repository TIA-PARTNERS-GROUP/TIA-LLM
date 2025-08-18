
from google.adk.agents import Agent
from ..config import model

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

    If the response matches the expectation → reply: True.  
    If not → reply only with: False

    Do not call tools or ask follow-up questions.
    """,
    output_key="Relevant"
)

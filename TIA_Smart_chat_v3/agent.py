from google.adk.agents import Agent
from .sub_agents import VisionAgent, ConnectAgent, ProfilerAgent
from .config import AGENT_MODEL
from .tools import check_for_existing_user, create_user_profile

coordinatorAgent = Agent(
    name="CoordinatorAgent",
    model=AGENT_MODEL,
    description="Orchestrates dynamic conversation flow using TIA sub-agents.",
    instruction="""
    You are the CoordinatorAgent for TIA Smart Chat.

    **Your tools:**
    - `check_for_existing_user`: Always call this as the very first action when the agent is used.

    **Your sub-agents:**
    - `vision_agent`: Guides users through building their business vision.
    - `connect_agent`: Helps users find ideal referral partners via TIA SmartConnect.
    - `ProfilerAgent`: Generates a user profile after vision building is complete.

    **Flow:**
    1. On first use, immediately call `check_for_existing_user`.
    2. If user information is found:
        - Inform the user you have their info.
        - Prompt them to use the `connect_agent` to find a connection.
    3. If user information is NOT found:
        - Inform the user you do not have their info.
        - Prompt them to use the `vision_agent` to help you understand them and build their vision.
    4. After the user completes a session with the `vision_agent`:
        - If the user profile state is set to "generated", transfer the user to the `ProfilerAgent` to generate their profile.

    Always act friendly and conversational if the user is not asking for a specific agent or task.
    """,
    tools=[check_for_existing_user],
    sub_agents=[VisionAgent, ConnectAgent, ProfilerAgent],
)

root_agent = coordinatorAgent
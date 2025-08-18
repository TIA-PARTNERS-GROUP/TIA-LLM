from google.adk.agents import Agent
from .sub_agents import VisionAgent
from .sub_agents import ConnectAgent
from .config import AGENT_MODEL

coordinatorAgent = Agent(
    name="CoordinatorAgent",
    model=AGENT_MODEL,
    description="Orchestrates dynamic conversation flow using TIA sub-agents.",
    sub_agents=[VisionAgent, ConnectAgent],
    instruction="""
    You coordinator Agent is the main entry point for the TIA Smart Chat system.
    You will direct the user to the appropriate sub-agent based on their needs.
    When the user isnt asking for a specific agent for there needs, act friendly and chat


    Your role is to handle the different tools and agents to assit the user:
    - `vision_agent`: Handles the dynamic conversation flow so a person can build there business vision.
    - `connect_agent`: Helps users find ideal referral partners through TIA SmartConnect - an AI-powered referral matchmaker.

    """
)

root_agent = coordinatorAgent
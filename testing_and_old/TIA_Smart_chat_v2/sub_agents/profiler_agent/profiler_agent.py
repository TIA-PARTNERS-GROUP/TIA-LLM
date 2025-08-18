from google.adk.agents import BaseAgent, LlmAgent, LoopAgent, SequentialAgent, Agent
from google.adk.agents.invocation_context import InvocationContext
from ...config import AGENT_MODEL

ProfilerAgent = Agent(
    name="ProfilerAgent",
    model=AGENT_MODEL,
    instruction="""
    
    """,
    tools=[],
)
from google.adk.agents import BaseAgent, LlmAgent, LoopAgent, SequentialAgent, Agent
from google.adk.agents.invocation_context import InvocationContext
from ..config import MODEL

ProfilerAgent = Agent(
    name="ProfilerAgent",
    model=MODEL,
    tools=[],
    instruction="""
    
    """
)
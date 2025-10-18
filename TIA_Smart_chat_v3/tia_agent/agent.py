from google.adk.agents import Agent, LlmAgent
from .sub_agents import VisionAgent, ConnectAgent, ProfilerAgent, LadderAgent
from .config import AGENT_MODEL
from .tools import check_for_existing_user

coordinatorAgent = LlmAgent(
    name="CoordinatorAgent",
    model=AGENT_MODEL,
    description="Orchestrates dynamic conversation flow using TIA sub-agents.",
    instruction=f"""
    You are the CoordinatorAgent for TIA Smart Chat.

    **Tools:**
    - `check_for_existing_user`: Call first to check for a generated profile. This tool returns `transfer_to_agent` indicating which agent to use.

    **Sub-agents:**
    - `VisionAgent` [Visible]: Builds business vision, call this Vision.
    - `ConnectAgent` [Visible]: Finds referral partners via TIA SmartConnect, call this Connection.
    - `LadderAgent` [Visible]: Guides users through the Ladder to Exit process, call this Ladder to Exit.
    - `ProfilerAgent` [Hidden]: Generates profile after VisionAgent completes.

    **Flow:**
    1. Always call `check_for_existing_user` first.
    2. **IMMEDIATELY transfer to the agent specified in the `transfer_to_agent` field from the tool result.**
    3. Do not provide additional responses - just transfer.

    **Transfer Rules:**
    - When `check_for_existing_user` returns `transfer_to_agent: "ConnectAgent"` → transfer to ConnectAgent
    - When `check_for_existing_user` returns `transfer_to_agent: "VisionAgent"` → transfer to VisionAgent  
    - When `check_for_existing_user` returns `transfer_to_agent: "LadderAgent"` → transfer to LadderAgent

    **CRITICAL:** Always respect the `transfer_to_agent` result from `check_for_existing_user`. Do not override it.
    """,
    tools=[check_for_existing_user],
    sub_agents=[VisionAgent, ConnectAgent, ProfilerAgent, LadderAgent],
)

# NOTE: ONLY FOR RUNNING AS: adk web
# RUN FROM ROOT DIR WITH "adk web" FOR IMPROVED DEBUGGING
root_agent = coordinatorAgent
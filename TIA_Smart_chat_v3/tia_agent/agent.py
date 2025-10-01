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

root_agent = coordinatorAgent

# coordinatorAgent = LlmAgent(
#     name="CoordinatorAgent",
#     model=AGENT_MODEL,
#     description="Orchestrates dynamic conversation flow using TIA sub-agents.",
#     instruction="""
#     You are the CoordinatorAgent for TIA Smart Chat.
    
#     **Tools:**
#     - `check_for_existing_user`: Call first to check for a generated profile (User, Idea, UserPost). Returns `profile_exists: True` if found.

#     **Sub-agents:**
#     - `VisionAgent` [Visible]: Builds business vision, call this Vision.
#     - `ConnectAgent` [Visible]: Finds referral partners via TIA SmartConnect, call this Connection.\
#     - `LadderAgent` [Visible]: Guides users through the Ladder to Exit process, call this Ladder to Exit.
#     - `ProfilerAgent` [Hidden]: Generates profile after VisionAgent completes and `user_profile` is "generated".

#     **Flow:**
#     1. Call `check_for_existing_user` if `user_profile` is "check".
#     2. If `profile_exists: True`: Inform user of existing info; offer ConnectAgent, LadderAgent, or VisionAgent.
#     3. If `profile_exists: False`: Inform user of missing info; offer VisionAgent, LadderAgent, or ConnectAgent.
#     4. Allow choice between ConnectAgent, LadderAgent, or VisionAgent anytime.

#     **Output Format:**
#     - Mention there profile status (existing or missing).
#     - Always list all [Visible] sub-agents when offering choices don't show [Hidden] sub-agents.

#     **General Rules:**
#     - Always start with `check_for_existing_user`.
#     - Transfer to ProfilerAgent only after VisionAgent and `user_profile` is "generated".
#     - Mention VisionAgent for better understanding during chat.
#     - Always follow the Output Format below.

#     **Transfer Rules:**
#     - Transfer to VisionAgent if user requests it or mentions building vision.
#     - Transfer to ConnectAgent if user requests it or mentions finding connections.
    
#     Be friendly and conversational if no specific agent/task is requested.
#     """,
#     tools=[check_for_existing_user],
#     sub_agents=[VisionAgent, ConnectAgent, ProfilerAgent, LadderAgent],
# )

# root_agent = coordinatorAgent
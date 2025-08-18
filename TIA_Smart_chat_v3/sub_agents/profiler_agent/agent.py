from google.adk.agents import BaseAgent, LlmAgent, LoopAgent, SequentialAgent, Agent
from google.adk.agents.invocation_context import InvocationContext
from .schemas import ProfileOutputSchema
from .tools import collect_user_history, store_user_profile
from ...config import AGENT_MODEL


# Collects the most recent user conversation history from the latest JSON file for profiling
HistoryCollectorAgent = LlmAgent(
    name="HistoryCollectorAgent",
    model=AGENT_MODEL,
    instruction="""
    Collect the user's most recent conversation history for profiling. 
    Use the collect_user_history tool to retrieve the latest JSON file containing the user's chat history.
    Output the full list of messages and questions as found in the file.
    """,
    tools=[collect_user_history],
    output_key="User_History"
)

# Generates a user profile from the user history and formats it for the GNN
ProfileGenerator = LlmAgent(
    name="ProfileGenerator",
    model=AGENT_MODEL,
    instruction="""
    You are given a list of conversation turns between the user and the assistant, where each turn contains a question and the user's answer.
    Your job is to analyze the conversation and extract the following information to fill out the user profile schema:

    - User: The user's full name.
    - Idea: The user's main business idea or what their company does.
    - UserPost: The user's job title or role.
    - Strength: The user's main strength, value, or unique impact as revealed in the conversation.

    Carefully read through all the user's responses. If information is missing, leave the field blank or use your best judgment based on context.
    Output the result as a JSON object matching the ProfileOutputSchema.

    Example input (conversation history):
    [
      {"question": "...", "message": "John Smith", ...},
      {"question": "...", "message": "Tech Innovations LLC", ...},
      {"question": "...", "message": "Founder and CEO", ...},
      {"question": "...", "message": "AI-powered customer service automation", ...},
      ...
    ]

    Example output:
    {
      "User": "John Smith",
      "Idea": "AI-powered customer service automation",
      "UserPost": "Founder and CEO",
      "Strength": "Helps business owners save time and focus on what they love" 
    }
    """,
    output_schema=ProfileOutputSchema,
    output_key="Generated_Profile"
)

# Stores the generated user profile in the database and GNN
ProfileStorer = LlmAgent(
    name="ProfileStorer",
    model=AGENT_MODEL,
    instruction="""
    Store the generated user profile in the database and the Graph Neural Network (GNN) using the store_user_profile tool.
    """,
    tools=[store_user_profile]
)

ProfilerAgent = SequentialAgent(
    name="ProfilerAgent",
    sub_agents=[
        HistoryCollectorAgent,
        ProfileGenerator,
        ProfileStorer
    ]
)
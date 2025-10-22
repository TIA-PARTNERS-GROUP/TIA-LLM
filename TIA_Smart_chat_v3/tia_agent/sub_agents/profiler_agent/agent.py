from google.adk.agents import LlmAgent, SequentialAgent, Agent
from .schemas import ProfileOutputSchema
from .tools import collect_user_history, store_user_profile
from ...config import AGENT_MODEL


# Collects the most recent user conversation history from the latest JSON file for profiling
HistoryCollectorAgent = LlmAgent(
    name="HistoryCollectorAgent",
    model=AGENT_MODEL,
    instruction="""
    Collect the user's most recent conversation history for profiling.
    Use the `collect_user_history` tool to retrieve the latest JSON file containing the user's chat history.
    
    **Important**:
    - At the end of your response add the tag <SILENT_AGENT>
    """,
    tools=[collect_user_history],
    output_key="User_History"
)

# Generates a user profile from the user history and formats it for the GNN
ProfileGenerator = LlmAgent(
    name="ProfileGenerator",
    model=AGENT_MODEL,
    description="Generates a user profile from conversation history, save to Database.",
    instruction="""
    You are given a list of conversation (User_History) turns between the user and the assistant, where each turn contains a question and the user's answer.
    Your job is to analyze the conversation and extract the following information to fill out the user profile schema:

    - Business_Name: The user's main business idea or what their company does (keep under 100 characters).
    - UserJob: The user's job title or role (keep under 100 characters).
    - User_Strength: The user's main strength, value, or unique impact as revealed in the conversation (keep under 100 characters to avoid DB limits).
    - User_skills: The user's skills as mentioned or inferred from the conversation. Format as short phrases (a couple of words each), separated by commas (e.g., "Python programming, Communication skills, Project Management"). Keep the total under 100 characters.
    - Business_Type: The type of business the user is involved in (keep under 100 characters).
    - Business_Strength: The strength of the user's business or job-related capabilities (keep under 100 characters).
    - Business_Skills: The skills related to the user's business (keep under 100 characters).
    - Business_Category: A singular categorising of the user's business (keep under 100 characters).
    - Skill_Category: A singular categorising of the user's skills (keep under 100 characters).
    - Strength_Category: A singular categorising of the user's strengths (keep under 100 characters).

    **Constraints**:
    - Keep all fields concise and under the specified character limits to ensure compatibility with the database.
    - If a field would exceed the limit, summarize or truncate it appropriately (e.g., for User_skills, list only the top 3-5 key skills as short phrases).
    - Carefully read through all the user's responses. Use your best judgment based on context.
    - Output the result as a JSON object matching the ProfileOutputSchema.

    **Important**: 
    - If you have received nothing about the user, return an empty profile with all fields blank and a summary stating "No profile information available." Do not make up information or use the example input and output as your response.
    - At the end of your response add the tag <SILENT_AGENT>
    """,
    output_schema=ProfileOutputSchema,
    output_key="Generated_Profile"
)

# Stores the generated user profile in the database and GNN
ProfileStorer = Agent(
    name="ProfileStorer",
    model=AGENT_MODEL,
    instruction="""
    1. Call the `store_user_profile` tool to save the generated user profile in both the database and the Graph Neural Network (GNN).
    2. Do not generate any user-facing response. Immediately transfer control to the `CoordinatorAgent` without displaying anything.

    **Important**:
    - Remain completely silent. Do not output any text, summary, or confirmation.
    - At the end of your response add the tag <SILENT_AGENT>
    """,
    tools=[store_user_profile]
)

# Assemble the ProfilerAgent as a SequentialAgent
ProfilerAgent = SequentialAgent(
    name="ProfilerAgent",
    sub_agents=[
        HistoryCollectorAgent,
        ProfileGenerator,
        ProfileStorer
    ]
)
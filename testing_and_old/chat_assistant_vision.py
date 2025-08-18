from google.adk.agents import BaseAgent, LlmAgent, LoopAgent, SequentialAgent, Agent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.models.lite_llm import LiteLlm

from ..config import model
from .sub_tools import save_conversation_entry, phase_checker_tool
from .prompts import (
    DYNAMIC_CHAT_RULE_PROMPT,
    TIA_VISION_CHAT_1_FOUNDATION_PROMPT,
    TIA_VISION_CHAT_2_REFLECTION_PROMPT,
    TIA_VISION_CHAT_3_ANALYSIS_PROMPT,
    TIA_VISION_CHAT_4_STRATEGY_PROMPT,
    TIA_VISION_BLOG_1_WHY_STATEMENT_PROMPT,
    TIA_VISION_BLOG_2_MESSAGING_PROMPT,
    TIA_VISION_BLOG_3_CONTENT_PROMPT
)

BLOG_AMOUNT = 3

CHAT_PROMPTS = [
    TIA_VISION_CHAT_1_FOUNDATION_PROMPT,
    TIA_VISION_CHAT_2_REFLECTION_PROMPT, 
    TIA_VISION_CHAT_3_ANALYSIS_PROMPT,
    TIA_VISION_CHAT_4_STRATEGY_PROMPT
]

phase_checker = LlmAgent(
    name="PhaseChecker",
    model=model,
    instruction="Check if the current phase should end based on the <END_OF_TIA_PROMPT tag>",
    output_key="phase_check"
)

# Create the 4 chat phase agents
foundation_agent = LlmAgent(
    name="FoundationPhase",
    model=model,
    instruction=DYNAMIC_CHAT_RULE_PROMPT.format(chat_prompt=TIA_VISION_CHAT_1_FOUNDATION_PROMPT),
    output_key="foundation_responses"
)

reflection_agent = LlmAgent(
    name="ReflectionPhase", 
    model=model,
    instruction=DYNAMIC_CHAT_RULE_PROMPT.format(chat_prompt=TIA_VISION_CHAT_2_REFLECTION_PROMPT),
    output_key="reflection_responses"
)

analysis_agent = LlmAgent(
    name="AnalysisPhase",
    model=model, 
    instruction=DYNAMIC_CHAT_RULE_PROMPT.format(chat_prompt=TIA_VISION_CHAT_3_ANALYSIS_PROMPT),
    output_key="analysis_responses"
)

strategy_agent = LlmAgent(
    name="StrategyPhase",
    model=model,
    instruction=DYNAMIC_CHAT_RULE_PROMPT.format(chat_prompt=TIA_VISION_CHAT_4_STRATEGY_PROMPT), 
    output_key="strategy_responses"
)

# Create blog generation agents
why_output = LlmAgent(
    name="WhyStatementGenerator",
    model=model,
    instruction=TIA_VISION_BLOG_1_WHY_STATEMENT_PROMPT,
    output_key="why_statement"
)

message_output = LlmAgent(
    name="BrandMessagingGenerator", 
    model=model,
    instruction=TIA_VISION_BLOG_2_MESSAGING_PROMPT,
    output_key="brand_messaging"
)

content_output = LlmAgent(
    name="ContentGenerator",
    model=model,
    instruction=TIA_VISION_BLOG_3_CONTENT_PROMPT,
    output_key="blog_content"
)

blog_agent = SequentialAgent(
    name="BlogContentGenerator",
    sub_agents=[why_output, message_output, content_output]
)

json_agent = LlmAgent(
    name="ConversationLogger",
    model=model,
    instruction="""
    You are responsible for logging conversation entries to a JSON file.
    
    For each question-answer pair in the conversation, extract:
    - The question that was asked
    - The phase it belongs to (Foundation, Reflection, Analysis, or Strategy)  
    - The user's answer/response
    
    Then call the save_conversation_entry tool with these parameters:
    - phase: The current conversation phase
    - question: The exact question that was asked
    - answer: The user's response to that question
    
    Always call save_conversation_entry for each question-answer pair you identify.
    """,
    tools=[save_conversation_entry],
    output_key="conversation_logged"
)

DynamicTIAAgent = Agent(
    name="VisionChatAgent",
    model=model,
    description="Handles dynamic business vision conversation phases and blog content generation.",
    sub_agents=[
        foundation_agent,
        reflection_agent,
        analysis_agent,
        strategy_agent,
        blog_agent,
        json_agent,
    ],
    tools=[phase_checker_tool],
    instruction="""
    You are a vision chat agent that orchestrates a dynamic business vision conversation.
    
    IMPORTANT: Follow this EXACT workflow:
    
    START IMMEDIATELY: When the conversation begins, automatically start with the Foundation Phase without waiting for user input.
    
    1. Foundation Phase (START HERE):
       - IMMEDIATELY call the `foundation_agent` to begin the conversation
       - After foundation_agent responds, call `phase_checker_tool` with the response text
       - If phase_checker_tool returns "PHASE_END", call `json_agent` to save the conversation, then move to step 2
       - If "PHASE_CONTINUE", stay in foundation phase and continue the conversation
    
    2. When Foundation Phase ends, move to Reflection Phase:
       - Call the `reflection_agent`
       - After reflection_agent responds, call `phase_checker_tool` with the response text
       - If phase_checker_tool returns "PHASE_END", call `json_agent` to save the conversation, then move to step 3
       - If "PHASE_CONTINUE", stay in reflection phase and continue the conversation
    
    3. When Reflection Phase ends, move to Analysis Phase:
       - Call the `analysis_agent`
       - After analysis_agent responds, call `phase_checker_tool` with the response text
       - If phase_checker_tool returns "PHASE_END", call `json_agent` to save the conversation, then move to step 4
       - If "PHASE_CONTINUE", stay in analysis phase and continue the conversation
    
    4. When Analysis Phase ends, move to Strategy Phase:
       - Call the `strategy_agent`
       - After strategy_agent responds, call `phase_checker_tool` with the response text
       - If phase_checker_tool returns "PHASE_END", call `json_agent` to save the conversation, then move to step 5
       - If "PHASE_CONTINUE", stay in strategy phase and continue the conversation
    
    5. After ALL 4 phases are complete, generate blog content:
       - Call the `blog_agent` to generate blog content based on all collected insights
    
    CRITICAL RULES:
    - START IMMEDIATELY with foundation_agent when the conversation begins
    - You MUST call `phase_checker_tool` after EVERY single response from any phase agent
    - Do not wait for user prompts to begin - start the Foundation Phase automatically
    """
)
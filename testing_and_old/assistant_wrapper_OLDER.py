import os
import sys
import json
import re
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from typing import AsyncGenerator
from typing_extensions import override

from google.adk.agents import BaseAgent, LlmAgent, LoopAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.models.lite_llm import LiteLlm

from pydantic import BaseModel, Field
from ..config import model

if __name__ == "__main__":
    from prompts import (
        DYNAMIC_CHAT_RULE_PROMPT,
        TIA_VISION_CHAT_1_FOUNDATION_PROMPT,
        TIA_VISION_CHAT_2_REFLECTION_PROMPT,
        TIA_VISION_CHAT_3_ANALYSIS_PROMPT,
        TIA_VISION_CHAT_4_STRATEGY_PROMPT,
        TIA_VISION_BLOG_1_WHY_STATEMENT_PROMPT,
        TIA_VISION_BLOG_2_MESSAGING_PROMPT,
        TIA_VISION_BLOG_3_CONTENT_PROMPT
    )
else:
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

class DynamicTIAAgent(BaseAgent):
    """Custom ADK agent with dynamic conversation state following Google ADK patterns."""
    
    # Pydantic field declarations for ADK compatibility - these are the individual agents
    foundation_agent: LlmAgent
    reflection_agent: LlmAgent
    analysis_agent: LlmAgent
    strategy_agent: LlmAgent
    why_output: LlmAgent
    message_output: LlmAgent
    content_output: LlmAgent
    phase_checker: LlmAgent
    
    # Composite agents
    blog_agent: SequentialAgent

    phase_amount: int
    
    model_config = {"arbitrary_types_allowed": True}
    
    def __init__(self, name: str):
        # Create the phase checker agent
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

        sub_agents_list = [
            phase_checker,
            foundation_agent,
            reflection_agent,
            analysis_agent,
            strategy_agent,
            blog_agent
        ]

        super().__init__(
            name=name,
            foundation_agent=foundation_agent,
            reflection_agent=reflection_agent,
            analysis_agent=analysis_agent,
            strategy_agent=strategy_agent,
            why_output=why_output,
            message_output=message_output, 
            content_output=content_output,
            phase_checker=phase_checker,
            blog_agent=blog_agent,
            sub_agents=sub_agents_list,
            phase_amount=len(CHAT_PROMPTS)
        )

        

    @override
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Implements the TIA conversation workflow with phase-based progression using SequentialAgent
        """
        logger = logging.getLogger(__name__)
        logger.info(f"[{self.name}] Starting TIA conversation workflow.")

        # Initialize session state if needed
        session_state = ctx.session.state
        if "current_phase" not in session_state:
            session_state["current_phase"] = 0
            session_state["chat_phases_complete"] = False
            session_state["tia_process_active"] = True
            session_state["tia_process_complete"] = False
            logger.info(f"[{self.name}] Initialized TIA session with phase 0")
        
        while not session_state.get("tia_process_complete") == True:
            session_state["tia_process_active"] = True
            current_phase = session_state.get("current_phase", 0)
            chat_complete = session_state.get("chat_phases_complete", False)
            
            logger.info(f"[{self.name}] Current phase: {current_phase}, Chat complete: {chat_complete}")

            # If chat phases are not complete, run the chat sequence
            if not chat_complete and current_phase < self.phase_amount:
                logger.info(f"[{self.name}] Running phase {current_phase}")
                
                # Get the current phase agent
                phase_agents = [self.foundation_agent, self.reflection_agent, self.analysis_agent, self.strategy_agent]
                current_agent = phase_agents[current_phase]
                
                # Check if we're waiting for user input
                if session_state.get("waiting_for_user", False):
                    # If there's a new user message, process it and continue
                    if ctx.session.messages and ctx.session.messages[-1].role == "user":
                        session_state["waiting_for_user"] = False
                        logger.info(f"[{self.name}] Received user response, continuing phase {current_phase}")
                    else:
                        # Still waiting for user input, don't yield any new events
                        logger.info(f"[{self.name}] Still waiting for user response in phase {current_phase}")
                        return
                
                # Run the current phase agent
                agent_responded = False
                async for event in current_agent.run_async(ctx):
                    # Store responses and check for phase transitions
                    if event.content and event.content.parts:
                        response_text = event.content.parts[0].text
                        session_state["last_assistant_response"] = response_text
                        agent_responded = True
                        
                        # Check for phase end marker
                        if re.search(r"<\s*END_OF_TIA_PROMPT\s*>", response_text, re.IGNORECASE):
                            current_phase += 1
                            session_state["current_phase"] = current_phase
                            session_state["waiting_for_user"] = False
                            logger.info(f"[{self.name}] Phase transition: moving to phase {current_phase}")
                            
                            # Check if all phases are complete
                            if current_phase >= self.phase_amount:
                                session_state["chat_phases_complete"] = True
                                logger.info(f"[{self.name}] All chat phases completed!")
                        else:
                            # Agent responded but phase isn't complete, wait for user
                            session_state["waiting_for_user"] = True
                            logger.info(f"[{self.name}] Agent responded, now waiting for user input")
                    
                    logger.info(f"[{self.name}] Event from Phase {current_phase}: {event.model_dump_json(indent=2, exclude_none=True)}")
                    yield event
                
                # If agent responded but we're not at phase end, wait for user
                if agent_responded and not session_state.get("chat_phases_complete", False):
                    if not re.search(r"<\s*END_OF_TIA_PROMPT\s*>", session_state.get("last_assistant_response", ""), re.IGNORECASE):
                        session_state["waiting_for_user"] = True
                        logger.info(f"[{self.name}] Phase {current_phase} continuing, waiting for user response")
                        return  # Exit and wait for next user input
                
                # Update local variables
                chat_complete = session_state.get("chat_phases_complete", False)
            
            # If we're here and chat_complete is True, proceed to blog generation
            if chat_complete:
                break
        
        logger.info(f"[{self.name}] All chat phases completed, generating blog content...")

        session_state["tia_process_complete"] = True
        session_state["tia_process_active"] = False
        
        # Prepare context for blog generation
        collected_context = self._format_context_for_blog(session_state)
        session_state["collected_context"] = collected_context
        
        logger.info(f"[{self.name}] Collected context prepared, starting blog generation...")

        # Generate blog content using the blog SequentialAgent
        async for event in self.blog_agent.run_async(ctx):
            logger.info(f"[{self.name}] Event from BlogAgent: {event.model_dump_json(indent=2, exclude_none=True)}")
            yield event

        logger.info(f"[{self.name}] TIA workflow iteration completed!")

    def _format_context_for_blog(self, session_state):
        """Format all collected responses into context for blog generation"""
        context_parts = []
        current_phase = session_state.get("current_phase", 0)
        
        # Extract responses from each completed phase
        phase_keys = [
            ("foundation_responses", "Foundation Phase"),
            ("reflection_responses", "Reflection Phase"), 
            ("analysis_responses", "Analysis Phase"),
            ("strategy_responses", "Strategy Phase")
        ]
        
        logger = logging.getLogger(__name__)
        logger.info(f"[_format_context_for_blog] Current phase: {current_phase}")
        logger.info(f"[_format_context_for_blog] Available keys in session: {list(session_state.keys())}")
        
        for phase_key, phase_name in phase_keys:
            if phase_key in session_state and session_state[phase_key]:
                response_text = session_state[phase_key]
                # Clean any remaining end tags
                cleaned_text = re.sub(r'<\s*END_OF_TIA_PROMPT\s*>', '', response_text, flags=re.IGNORECASE).strip()
                context_parts.append(f"{phase_name}: {cleaned_text}")
                logger.info(f"[_format_context_for_blog] Added {phase_name} content")
        
        # Also check for any conversation history or user responses
        if "conversation_history" in session_state:
            conv_history = session_state["conversation_history"]
            if isinstance(conv_history, list) and conv_history:
                # Extract user messages from conversation history
                user_messages = [msg.get("content", "") for msg in conv_history if msg.get("role") == "user"]
                if user_messages:
                    context_parts.append(f"User Responses: {' | '.join(user_messages)}")
                    logger.info(f"[_format_context_for_blog] Added conversation history with {len(user_messages)} user messages")
        
        final_context = "\n\n".join(context_parts) if context_parts else "No context available"
        
        logger.info(f"[_format_context_for_blog] Final context length: {len(final_context)} characters")
        return final_context
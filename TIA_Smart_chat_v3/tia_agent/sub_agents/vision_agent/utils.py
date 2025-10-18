from ..DynamicChatAssistant import generate_response
from .prompts import (
    TIA_VISION_BLOG_1_WHY_STATEMENT_PROMPT,
    TIA_VISION_BLOG_2_MESSAGING_PROMPT,
    TIA_VISION_BLOG_3_CONTENT_PROMPT
)
import logging

logger = logging.getLogger(__name__)

BLOG_AMOUNT = 1

def generate_content_why_statement(collected_context):
    """Generate Why Statement using collected responses"""
    try:
        logger.debug("[Generating Why Statement]")
        why_prompt = TIA_VISION_BLOG_1_WHY_STATEMENT_PROMPT.format(collected_context=collected_context)
        input_messages = [
            {"role": "system", "content": why_prompt},
            {"role": "user", "content": "Please generate my Why Statement based on the context provided."}
        ]
        return generate_response(input_messages)
    except Exception as e:
        logger.error(f"Error generating Why Statement: {e}")
        return "Error generating Why Statement."

def generate_content_messaging(collected_context):
    """Generate messaging (taglines, slogans, bios) using collected responses"""
    try:
        logger.debug("[Generating messaging elements]")
        messaging_prompt = TIA_VISION_BLOG_2_MESSAGING_PROMPT.format(collected_context=collected_context)
        input_messages = [
            {"role": "system", "content": messaging_prompt},
            {"role": "user", "content": "Please generate messaging elements including taglines, slogans, and bio based on the context."}
        ]
        return generate_response(input_messages)
    except Exception as e:
        logger.error(f"Error generating messaging elements: {e}")
        return "Error generating messaging elements."

def generate_content_blog(collected_context, blog_amount=BLOG_AMOUNT):
    """Generate blog content and social captions using collected responses"""
    try:
        all_content = []
        for i in range(blog_amount):
            logger.debug(f"[Generating content batch {i+1}/{blog_amount}]")
            content_prompt = TIA_VISION_BLOG_3_CONTENT_PROMPT.format(collected_context=collected_context)
            input_messages = [
                {"role": "system", "content": content_prompt},
                {"role": "user", "content": f"Please generate blog content batch {i+1} with social media captions based on the context."}
            ]
            
            # Add generation break at the start
            blog_content = "<GENERATION_BREAK>\n"
            
            assistant_response = generate_response(input_messages)
            
            # Add the content with batch header and generation break at the end
            blog_content += f"---\n\n## CONTENT BATCH {i+1}\n\n---\n\n{assistant_response}\n\n<GENERATION_BREAK>"
            
            all_content.append(blog_content)
        
        return "\n".join(all_content)
    except Exception as e:
        logger.error(f"Error generating blog content: {e}")
        return "Error generating blog content."
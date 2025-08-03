# TIA Vision Assistant with Response Recording

This enhanced version of the TIA Vision Assistant automatically records user responses through all conversation phases and uses them to generate personalized blog content.

## Features

### 🎯 **Automatic Phase Progression**
- **Phase 1**: Personal & Business Foundation (Questions 0-4)
- **Phase 2**: Vision & Reflection (Questions 5-11) 
- **Phase 3**: Business Analysis (Questions 12-20)
- **Phase 4**: Strategy & Messaging (Questions 21-30)
- **Phase 5**: Blog Content Generation (Automatic)

### 📝 **Response Recording**
- Records all user responses with structured mapping
- Saves responses to JSON files automatically
- Tracks conversation progress and phase transitions
- Provides status commands for real-time progress monitoring

### 🤖 **Smart Content Generation**
- Uses collected responses to generate personalized blog content
- Creates 12 blog headlines, 12 blog posts, and 12 social media captions
- Content is tailored to the user's business, values, and messaging tone

## Files

- `assistant_wrapper.py` - Main assistant class with recording functionality
- `prompts.py` - All conversation prompts for each phase
- `phase_config.py` - Phase definitions and question mapping
- `demo_with_recording.py` - Demo script and testing utilities

## Usage

### Interactive Chat
```python
from assistant_wrapper import AssistantWrapper

assistant = AssistantWrapper()
assistant.chat_loop()
```

### Commands During Chat
- `quit/exit/bye` - End conversation and save responses
- `save` - Save current responses to file
- `status` - Show current progress and phase info

### Demo Mode
```bash
python demo_with_recording.py
```
Choose option 1 for automated demo with sample responses.

## Response Structure

The assistant records responses in this JSON structure:

```json
{
  "foundation": {
    "name": "User's name",
    "company_name": "Company name",
    "role": "User's role",
    "product_service": "What they offer",
    "target_customer": "Who they serve"
  },
  "reflection": {
    "initial_vision": "Original business vision",
    "current_feelings": "Current business feelings",
    "human_impact": "Human impact of service",
    "success_story": "Success story example",
    "ideal_client_feedback": "Desired client feedback",
    "deeper_impact": "Deeper work impact",
    "team_feelings": "Desired team feelings"
  },
  "analysis": {
    "product_improvement": "Product improvement ideas",
    "market_expansion": "Market expansion thoughts",
    "expansion_suggestions": "Expansion preferences",
    "competition_differentiation": "Competitive differentiation",
    "industry_frustrations": "Industry pain points",
    "overlooked_needs": "Unmet customer needs",
    "industry_changes": "Desired industry changes",
    "unique_beliefs": "Unique business beliefs",
    "profitability": "Profitability assessment"
  },
  "strategy": {
    "action_plan_or_why": "Next step preference",
    "tone_selection": "Chosen brand tone",
    "tone_refinement": "Tone refinement",
    "why_statement_final": "Final Why Statement",
    "messaging_next": "Messaging preferences",
    "messaging_tone": "Messaging tone",
    "content_creation": "Content creation preferences",
    "blog_format": "Blog format preferences",
    "document_title": "Document title",
    "review_preference": "Review preferences"
  },
  "session_info": {
    "start_time": "2025-01-01T10:00:00.000Z",
    "end_time": "2025-01-01T11:00:00.000Z",
    "current_question": 30
  }
}
```

## Content Generation

At the end of the conversation (after question 30), the assistant automatically:

1. **Formats** all collected responses into structured context
2. **Generates** personalized content using the TIA_VISION_BLOG_PROMPT
3. **Creates**:
   - 12 Blog Post Headlines
   - 12 Blog Posts (150-250 words each)
   - 12 Social Media Captions
4. **Saves** everything to a timestamped JSON file

## Environment Setup

Create a `.env` file with:
```
OPENAI_API_KEY=your_openai_api_key
OPENAI_ASSISTANT_ID=your_assistant_id
```

## Example Output

After completing all phases, you'll get:
- `tia_responses_YYYYMMDD_HHMMSS.json` - All recorded responses
- Generated blog content in the final assistant response
- Complete conversation history preserved

The assistant provides a seamless experience that guides users through discovery while building a comprehensive profile for content generation.

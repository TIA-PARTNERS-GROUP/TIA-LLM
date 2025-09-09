from litellm import completion
from .tia_agent.config import OPENAI_API_KEY

def compare_responses(actual: str, expected: str) -> float:
    """
    Uses litellm to compare actual and expected responses by prompting an LLM to rate similarity.
    Returns a score from 0 to 10.
    """
    prompt = f"Rate the similarity between these two responses on a scale of 0 to 10, where 10 is identical and 0 is completely different. Only return the number as a float.\n\nActual: {actual}\n\nExpected: {expected}"
    
    try:
        response = completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            api_key=OPENAI_API_KEY,
            max_tokens=10,
            temperature=0.0
        )
        score_text = response.choices[0].message.content.strip()
        score = float(score_text)
        return max(0.0, min(10.0, score))
    except Exception as e:
        print(f"Error in comparison: {e}")
        return 0.0
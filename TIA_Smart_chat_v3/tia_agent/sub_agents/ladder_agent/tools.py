from google.adk.tools.tool_context import ToolContext
from typing import Dict

def generate_ladder_results(tool_context: ToolContext, ladder_scores: Dict[str, int]) -> dict:
    """
    Store the chat messages in the LadderAgent state.
    
    Args:
        ladder_scores: Dictionary containing scores for each category (1-10)
                      e.g., {"clarity": 7, "workload": 5, "cashflow": 8, "support": 6, "inspiration": 9}
    """
    try:
        state = tool_context.state
        ladder_state = state.get("LadderAgent", {})
        
        # Validate that we have the expected keys
        expected_keys = ["clarity", "workload", "cashflow", "support", "inspiration"]
        
        results = {}
        for key in expected_keys:
            results[key] = ladder_scores[key]
        
        ladder_state["results"] = results
        state["LadderAgent"] = ladder_state
        
        return {
            "status": "success", 
            "message": "Ladder scores stored successfully",
            "results": results
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
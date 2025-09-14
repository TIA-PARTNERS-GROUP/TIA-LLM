from typing import Dict, Any, List
from dotenv import load_dotenv
from litellm import completion
from urllib.parse import urlencode
from ...config import CHAT_MODEL, OPENAI_API_KEY, RAPIDAPI_HOST, RAPIDAPI_KEY
from .prompts import CONNECT_GENERATION_PROMPT
import os, requests, json, http.client

load_dotenv()

def extract_business_type(conversation_history):
    """Extract business_type from conversation history using LLM."""
    print(f"DEBUG: Conversation history for business_type extraction: {conversation_history}")
    
    business_type_prompt = f"""
    Analyze the following conversation history and determine the most appropriate business_type for the user.
    Business_type should be a short phrase of 2-3 words max (e.g., "AI Consulting", "Tech Automation").
    Keep it under 50 characters.

    Conversation:
    {conversation_history}

    Output only the business_type as a string.
    """
    input_messages = [
        {"role": "system", "content": "You are an assistant that extracts short business types from conversations."},
        {"role": "user", "content": business_type_prompt}
    ]
    business_type = completion(
        model=CHAT_MODEL,
        messages=input_messages,
        api_key=OPENAI_API_KEY
    ).choices[0].message.content.strip()
    
    return business_type
    
def search_businesses_in_area(business_type: str, limit: int, region: str, zoom: int, lat: float, lng: float, language: str = "en",) -> dict:
    params = {
        "query": business_type,
        "lat": f"{lat:.6f}",
        "lng": f"{lng:.6f}",
        "limit": str(limit),
        "language": language,
        "region": region,
        "zoom": zoom,
        "extract_emails_and_contacts": str(True).lower(),
    }

    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY,
    }

    conn = http.client.HTTPSConnection(RAPIDAPI_HOST, timeout=30)
    try:
        path = f"/search-in-area?{urlencode(params)}"
        conn.request("GET", path, headers=headers)
        res = conn.getresponse()
        body = res.read()
        if res.status != 200:
            raise RuntimeError(f"HTTP {res.status}: {body.decode('utf-8', 'ignore')}")
        return json.loads(body)
    finally:
        conn.close()

def recommended_WEB_connection(attributes: Dict[str, Any]) -> dict:
    """
    Fallback: Uses LLM to turn attributes into a business query, then searches RapidAPI.
    """
    #business_type = attributes.get("business_type", "") # STILL NEED TO TEST ONCE AGENT IS HOOKED UP TO SITE

    region = attributes.get("region", "au")
    lat = attributes.get("lat", 0.0)
    lng = attributes.get("lng", 0.0)
    limit = 5
    zoom = 10

    # Compose a prompt for the LLM to generate a business query string
    message = [
        {"role": "system", "content": "You are an assistant that generates concise business search queries for local business data APIs."},
        {"role": "user", "content": f"Attributes: {json.dumps(attributes.get("profile"))}\nTurn these into a business search query string for finding relevant businesses."}
    ]
    query = completion(
        model=CHAT_MODEL,
        messages=message,
        api_key=OPENAI_API_KEY
    ).choices[0].message.content.strip()

    print(f"DEBUG: Generated query: {query}")

    try:
        results = search_businesses_in_area(query, limit, region, zoom, lat, lng)
        return results
    except Exception as e:
        print(f"Error in recommended_WEB_connection: {e}")
        return {"error": str(e)}

def recommended_GNN_connection(attributes: Dict[str, Any]):
    """
    Connects to the complementary partners API to retrieve recommended businesses.
    Expects attributes to contain user_id.
    """
    user_id = attributes.get("user_id")
    if not user_id:
        print("Error: user_id not found in attributes")
        return None

    # API base URL
    api_base_url = os.getenv("GNN_API_BASE_URL")
    url = f"{api_base_url}/user/{user_id}/complementary_partners"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()  # Return the list of recommendations
    except Exception as e:
        print(f"Error connecting to complementary partners API: {e}")
        return None
    
def generate_email_templates(businesses, user_name, user_job, user_email, business_name):
    """Generate email templates for a list of businesses."""
    email_templates = []
    # TODO: Implement connection_result
    for business in businesses:
        name = business.get("name")
        email = business.get("emails_and_contacts", {}).get("emails", [""])[0] if business.get("emails_and_contacts", {}).get("emails") else ""
        address = business.get("full_address")
        website = business.get("website")
        phone = business.get("phone_number")
        rating = business.get("rating")
        review_count = business.get("review_count")
        business_type = business.get("type")
        opening_status = business.get("opening_status")
        about_summary = business.get("about", {}).get("summary") if business.get("about") else ""

        
        # Prompt for generating a personalized email template
        email_prompt = CONNECT_GENERATION_PROMPT.format(
            name=name,
            email=email,
            address=address,
            website=website,
            phone=phone,
            rating=rating,
            review_count=review_count,
            business_type=business_type,
            opening_status=opening_status,
            about_summary=about_summary,
            user_name=user_name,
            user_job=user_job,
            user_email=user_email,
            business_name=business_name
        )
        
        input_messages = [
            {"role": "system", "content": "You are an assistant that generates professional email templates for business outreach."},
            {"role": "user", "content": email_prompt}
        ]
        email_output = completion(
            model=CHAT_MODEL,
            messages=input_messages,
            api_key=OPENAI_API_KEY
        ).choices[0].message.content.strip()
        
        email_templates.append({
            "business_name": name,
            "email": email,
            "phone": phone,
            "rating": rating,
            "review_count": review_count,
            "business_type": business_type,
            "template": email_output
        })
    
    return email_templates
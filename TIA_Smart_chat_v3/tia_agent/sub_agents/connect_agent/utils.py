from typing import Dict, Any
from dotenv import load_dotenv
from urllib.parse import urlencode
from ...config import RAPIDAPI_HOST, RAPIDAPI_KEY
from .prompts import CONNECT_GENERATION_PROMPT
from ..DynamicChatAssistant import generate_response
import os, requests, json, http.client, logging

load_dotenv()

logger = logging.getLogger(__name__)

def extract_business_type(conversation_history):
    """Extract business_type from conversation history using LLM."""
    logger.debug(f"Conversation history for business_type extraction: {conversation_history}")
    
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
    
    business_type = generate_response(input_messages)
    
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
    Fallback: Generates a query based on connection_type-specific attributes, then searches RapidAPI.
    """
    connection_type = attributes.get("connection_type", "complementary")
    connect_agent = attributes.get("ConnectAgent", {})
    profile = attributes.get("profile", {})
    region = attributes.get("region", "au")
    lat = attributes.get("lat", 0.0)
    lng = attributes.get("lng", 0.0)
    limit = 5
    zoom = 10

    # Select attributes based on connection_type
    chat_attributes = connect_agent.get("connection_type")
    if chat_attributes:
        selected_attributes = chat_attributes

    else:
        attribute_mappings = {
            "complementary": ["Business_Type", "Business_Category", "Business_Name"],
            "alliance": ["Project_Required_Skills", "User_skills", "Business_Skills"],
            "mastermind": ["User_Strength"],
            "intelligent": ["User_skills", "Business_Type", "Business_Name"],
        }
    
        required_fields = attribute_mappings.get(connection_type, ["Business_Type"])
        selected_attributes = {k: v for k, v in profile.items() if k in required_fields}
    
    # Compose a prompt for the LLM to generate a business query string
    message = [
        {"role": "system", "content": "You are an assistant that generates concise business search queries for local business data APIs."},
        {"role": "user", "content": f"Connection Type: {connection_type}\nSelected Attributes: {json.dumps(selected_attributes)}\nGenerate a 1-5 word search query that best fits this for finding relevant businesses."}
    ]
    query = generate_response(message)

    logger.debug(f"Generated query for {connection_type}: {query}")

    try:
        results = search_businesses_in_area(query, limit, region, zoom, lat, lng)
        return results
    except Exception as e:
        logger.error(f"Error in recommended_WEB_connection for {connection_type}: {e}")
        return {"error": str(e)}

def recommended_GNN_connection(attributes: Dict[str, Any]):
    """
    Connects to different APIs based on connection_type to retrieve recommended businesses.
    Expects attributes to contain user_id and connection_type.
    """
    user_id = attributes.get("user_id")
    connection_type = attributes.get("connection_type", "complementary")
    if not user_id:
        logger.error("Error: user_id not found in attributes")
        return None

    # API base URL
    api_base_url = os.getenv("GNN_API_BASE_URL")
    
    # Different endpoints for each connection type
    endpoints = {
        "complementary": f"{api_base_url}/user/{user_id}/complementary_partners",
        "alliance": f"{api_base_url}/user/{user_id}/alliance_partners",
        "mastermind": f"{api_base_url}/user/{user_id}/mastermind_partners",
        "intelligent": f"{api_base_url}/user/{user_id}/intelligent_partners",
    }
    
    url = endpoints.get(connection_type)
    
    try:
        #response = requests.get(url, timeout=10)
        #response.raise_for_status()

        # TESTING MOCK RESPONSE
        response = [
            {
                "recommendation": {
                    "user": {
                        "id": 101,
                        "name": "Sarah Chen",
                        "business": "Digital Marketing Pro",
                        "type": "Marketing Agency",
                        "category": "Digital Marketing",
                        "description": "Specializes in social media and online advertising campaigns"
                    }
                },
                "reason": "COMPLEMENTARY PARTNER: Perfect for mutual client referrals. You can recommend their digital marketing services to your clients while they refer web development projects to you. Everyone wins—your clients save time, your partner gains business, and you earn referral margins.",
            },
            {
                "recommendation": {
                    "user": {
                        "id": 102,
                        "name": "Mike Rodriguez",
                        "business": "WebFlow Masters",
                        "type": "Web Development",
                        "category": "Website Development",
                        "description": "Creates high-converting landing pages and business websites"
                    }
                },
                "reason": "COMPLEMENTARY PARTNER: Ideal for cross-promotion. Their web development expertise complements your services. Share clients who need both your offerings—increasing client satisfaction and creating new revenue streams for both businesses.",
            },
            {
                "recommendation": {
                    "user": {
                        "id": 103,
                        "name": "Jessica Wong",
                        "business": "Content Creators Co",
                        "type": "Content Creation",
                        "category": "Content Marketing",
                        "description": "Produces engaging blog content and video marketing materials"
                    }
                },
                "reason": "COMPLEMENTARY PARTNER: Strong alignment for bundled services. Combine your offerings with their content creation to provide complete solutions. Refer clients to each other for comprehensive service packages.",
            }
        ]
        return response.json()
    except Exception as e:
        logger.error(f"Error connecting to {connection_type} partners API: {e}")
        return None
    
def generate_email_templates(businesses, user_name, user_job, user_email, business_name):
    """Generate email templates for a list of businesses."""
    email_templates = []
    
    for business in businesses:
        name = business.get("name", "Unknown")
        email = business.get("emails_and_contacts", "Unknown").get("emails", ["Unknown"])[0] if business.get("emails_and_contacts", "Unknown").get("emails") else "Unknown"
        address = business.get("full_address", "Unknown")
        website = business.get("website", "Unknown")
        phone = business.get("phone_number", "Unknown")
        rating = business.get("rating", "Unknown")
        review_count = business.get("review_count", "Unknown")
        business_type = business.get("type", "Unknown")
        opening_status = business.get("opening_status", "Unknown")
        about_summary = business.get("about", {}).get("summary", "Unknown")

        try:
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
            email_output = generate_response(input_messages)
            
            email_output += "\n<GENERATION_BREAK>"
            
            email_templates.append({
                "business_name": name,
                "email": email,
                "phone": phone,
                "rating": rating,
                "review_count": review_count,
                "business_type": business_type,
                "template": email_output
            })
        except Exception as e:
            logger.error(f"Error generating email for {name}: {e}")
            email_templates.append({
                "business_name": name,
                "email": email,
                "template": f"Error: {str(e)}\n<GENERATION_BREAK>"
            })
    
    return email_templates
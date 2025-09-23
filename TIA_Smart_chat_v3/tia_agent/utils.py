
import pymysql
import os

def get_user_details(cursor, user_id):
    """Get user details from database."""
    cursor.execute("SELECT first_name, last_name, contact_email, contact_phone_no FROM users WHERE id = %s", (user_id,))
    user_result = cursor.fetchone()
    if not user_result:
        return None
    first_name, last_name, contact_email, contact_phone_no = user_result
    return first_name, last_name, contact_email, contact_phone_no

def get_business_details(cursor, user_id):
    """Get business details from database."""
    cursor.execute("SELECT name, contact_email, contact_phone_no FROM businesses WHERE operator_user_id = %s", (user_id,))
    business_result = cursor.fetchone()
    if not business_result:
        return None, None, None
    business_name, business_email, business_phone = business_result
    return business_name, business_email, business_phone

def get_user_skills(cursor, user_id):
    """Get user skills as string."""
    cursor.execute("""
        SELECT s.name FROM skills s
        JOIN user_skills us ON s.id = us.skill_id
        WHERE us.user_id = %s
    """, (user_id,))
    user_skills = [row[0] for row in cursor.fetchall()]
    return ", ".join(user_skills)

def get_user_strengths(cursor, user_id):
    """Get user strengths as string."""
    cursor.execute("""
        SELECT s.name FROM strengths s
        JOIN user_strengths us ON s.id = us.strength_id
        WHERE us.user_id = %s
    """, (user_id,))
    user_strengths = [row[0] for row in cursor.fetchall()]
    return ", ".join(user_strengths)

def get_business_strengths(cursor, user_id):
    """Get business strengths as string."""
    cursor.execute("""
        SELECT bs.name FROM business_strengths bs
        JOIN user_business_strengths ubs ON bs.id = ubs.business_strength_id
        WHERE ubs.user_id = %s
    """, (user_id,))
    business_strengths = [row[0] for row in cursor.fetchall()]
    return ", ".join(business_strengths)

def get_business_skills(cursor, user_id):
    """Get business skills as string."""
    cursor.execute("""
        SELECT s.name FROM skills s
        JOIN user_skills us ON s.id = us.skill_id
        WHERE us.user_id = %s AND s.category_id IN (
            SELECT id FROM skill_categories WHERE name LIKE 'Business%%'
        )
    """, (user_id,))
    business_skills = [row[0] for row in cursor.fetchall()]
    return ", ".join(business_skills)

def get_business_type(cursor, user_id):
    """Get business type."""
    cursor.execute("""
        SELECT bt.name FROM business_types bt
        JOIN businesses b ON bt.id = b.business_type_id
        WHERE b.operator_user_id = %s
    """, (user_id,))
    business_type_result = cursor.fetchone()
    return business_type_result[0] if business_type_result else None

def get_business_category(cursor, user_id):
    """Get business category."""
    cursor.execute("""
        SELECT bc.name FROM business_categories bc
        JOIN businesses b ON bc.id = b.business_category_id
        WHERE b.operator_user_id = %s
    """, (user_id,))
    business_category_result = cursor.fetchone()
    return business_category_result[0] if business_category_result else None


def get_user_job(cursor, user_id):
    """Get user job."""
    cursor.execute("""
        SELECT br.name FROM business_roles br
        JOIN business_strengths bs ON br.id = bs.business_role_id
        JOIN user_business_strengths ubs ON bs.id = ubs.business_strength_id
        WHERE ubs.user_id = %s LIMIT 1
    """, (user_id,))
    user_job_result = cursor.fetchone()
    return user_job_result[0] if user_job_result else None

def load_user_profile(user_id: int):
    """Load user profile from database. Returns dict with status, profile_exists, and profile if available."""
    try:
        print(f"DEBUG: Loading profile for user ID: {user_id}")

        # Connect to DB
        conn = pymysql.connect(
            host=os.environ["DB_HOST"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASS"],
            database=os.environ["DB_NAME"],
            port=int(os.environ.get("DB_PORT", 3306))
        )
        cursor = conn.cursor()
        print("DEBUG: Connected to DB")

        # Get user details
        user_details = get_user_details(cursor, user_id)
        print(f"DEBUG: User details retrieved: {user_details}")
        if not user_details:
            cursor.close()
            conn.close()
            return {"status": "success", "profile_exists": False, "message": "User not found in database."}

        first_name, last_name, _, _ = user_details

        # Get business details
        # BUG
        business_name, business_email, business_phone = get_business_details(cursor, user_id)
        print(f"DEBUG: Business details retrieved: {business_name}, {business_email}, {business_phone}")

        # Get user skills
        user_skills_str = get_user_skills(cursor, user_id)
        print(f"DEBUG: User skills retrieved: {user_skills_str}")

        # Get business skills
        business_skills_str = get_business_skills(cursor, user_id)
        print(f"DEBUG: Business skills retrieved: {business_skills_str}")

        # Get user strengths
        user_strengths_str = get_user_strengths(cursor, user_id)
        print(f"DEBUG: User strengths retrieved: {user_strengths_str}")

        # Get business strengths
        business_strengths_str = get_business_strengths(cursor, user_id)
        print(f"DEBUG: Business strengths retrieved: {business_strengths_str}")

        # Get business type
        business_type = get_business_type(cursor, user_id)
        print(f"DEBUG: Business type retrieved: {business_type}")

        # Get business category
        business_category = get_business_category(cursor, user_id)
        print(f"DEBUG: Business category retrieved: {business_category}")

        # Get user job
        user_job = get_user_job(cursor, user_id)
        print(f"DEBUG: User job retrieved: {user_job}")

        cursor.close()
        conn.close()
        print("DEBUG: DB connection closed")

        # Check if essential profile data exists
        profile_exists = bool(business_name and user_job and user_strengths_str and user_skills_str and business_strengths_str and business_type and business_skills_str)
        print(f"DEBUG: Profile exists: {profile_exists}")

        profile = {
            "UserName": f"{first_name} {last_name}",
            "Business_Name": business_name,
            "Contact_Email": business_email,
            "Contact_Phone_No": business_phone
        }
        
        #profile_exists = False # DISABLE FOR TESTING
        
        if profile_exists:
            # Construct and set the profile
            profile.update({
                "Business_Type": business_type,
                "UserJob": user_job,
                "User_Strength": user_strengths_str,
                "User_skills": user_skills_str,
                "Business_Strength": business_strengths_str,
                "Business_Skills": business_skills_str,
                "Business_Category": business_category,
            })
            print(f"DEBUG: Profile data: {profile}")
            return {"status": "success", "profile_exists": True, "profile": profile}
        else:
            return {"status": "success", "profile_exists": False, "profile": profile}

    except Exception as e:
        print(f"DEBUG: Error in load_user_profile: {e}")
        return {"status": "error", "message": str(e)}
    
def validate_connection_options(connection_type: str, profile: dict = None):
    """Validate connection options and check if the loaded profile data is valid for the connection type."""
    valid_types = {"complementary", "alliance", "mastermind", "intelligent"}
    if connection_type not in valid_types:
        return False, f"Invalid connection type '{connection_type}'. Must be one of {valid_types}."
    
    if not profile:
        return False, "Profile data is required for validation."
    
    # Define required fields for each connection type based on data requirements
    requirements = {
        "intelligent": ["User_skills", "Business_Type", "Business_Name"],
        "complementary": ["Business_Type", "Business_Category", "Business_Name"],
        "alliance": ["Project_Required_Skills", "User_skills", "Business_Skills"],
        "mastermind": ["User_Strength"],
    }
    
    required_fields = requirements.get(connection_type, [])
    missing_fields = []
    
    for field in required_fields:
        value = profile.get(field)
        if not value or (isinstance(value, str) and value.strip() == ""):
            missing_fields.append(field)
    
    if missing_fields:
        return False, f"Profile is invalid for '{connection_type}' connection. Missing or empty fields: {', '.join(missing_fields)}."
    
    return True, f"Profile is valid for '{connection_type}' connection."
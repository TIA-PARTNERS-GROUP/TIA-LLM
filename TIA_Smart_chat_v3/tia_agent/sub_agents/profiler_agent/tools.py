from google.adk.tools import ToolContext
from datetime import datetime
import os, json, re
import pymysql

generation_catergory_type = "TIA Agent Generated"

def ensure_business_type_and_categories(cursor, business_type: str):
    """Ensure business type, skill category, and strength category exist. Returns IDs or raises exception."""
    try:
        print("DEBUG: Ensuring business type and categories for:", business_type)
        
        # Ensure business type exists
        cursor.execute("SELECT id FROM business_types WHERE name=%s", (business_type,))
        result = cursor.fetchone()
        if result:
            business_type_id = result[0]
        else:
            cursor.execute("INSERT INTO business_types (name) VALUES (%s)", (business_type,))
            business_type_id = cursor.lastrowid
        
        # Ensure skill category exists (fixed column name to business_type_id)
        cursor.execute("SELECT id FROM skill_categories WHERE name=%s", (generation_catergory_type,))
        result = cursor.fetchone()
        if result:
            skill_category_id = result[0]
        else:
            cursor.execute(
                "INSERT INTO skill_categories (name, business_type_id) VALUES (%s, %s)", 
                (generation_catergory_type, business_type_id)
            )
            skill_category_id = cursor.lastrowid
        
        # Ensure strength category exists
        cursor.execute("SELECT id FROM strength_categories WHERE name=%s", (generation_catergory_type,))
        result = cursor.fetchone()
        if result:
            strength_category_id = result[0]
        else:
            cursor.execute("INSERT INTO strength_categories (name) VALUES (%s)", (generation_catergory_type,))
            strength_category_id = cursor.lastrowid
        
        return business_type_id, skill_category_id, strength_category_id
    except Exception as e:
        print("ERROR in ensure_business_type_and_categories:", e)
        raise e

def ensure_business_phase_and_role(cursor, user_role: str):
    """Ensure business phase and role exist. Returns IDs or raises exception."""
    try:
        print("DEBUG: Ensuring business phase and role")
        
        # Ensure business phase exists
        cursor.execute("SELECT id FROM business_phases WHERE name=%s", ("TIA Agent Chatting",))
        result = cursor.fetchone()
        if result:
            chat_test_phase_id = result[0]
        else:
            cursor.execute("INSERT INTO business_phases (name) VALUES (%s)", ("TIA Agent Chatting",))
            chat_test_phase_id = cursor.lastrowid
        
        # Ensure business role exists
        cursor.execute("SELECT id FROM business_roles WHERE name=%s", (user_role,))
        result = cursor.fetchone()
        if result:
            business_role_id = result[0]
        else:
            cursor.execute("INSERT INTO business_roles (name) VALUES (%s)", (user_role,))
            business_role_id = cursor.lastrowid
        
        return chat_test_phase_id, business_role_id
    except Exception as e:
        print("ERROR in ensure_business_phase_and_role:", e)
        raise e

def insert_user_skills(cursor, user_id: int, user_skills: list, skill_category_id: int):
    """Insert user skills. Raises exception on failure."""
    try:
        print("DEBUG: Inserting user skills:", user_skills)
        for skill in user_skills:
            cursor.execute("INSERT IGNORE INTO skills (name, category_id) VALUES (%s, %s)", (skill, skill_category_id))
            cursor.execute("INSERT IGNORE INTO user_skills (user_id, skill_id) SELECT %s, id FROM skills WHERE name=%s", (user_id, skill))
    except Exception as e:
        print("ERROR in insert_user_skills:", e)
        raise e

def insert_user_strengths(cursor, user_id: int, user_strengths: list, strength_category_id: int):
    """Insert user strengths. Raises exception on failure."""
    try:
        print("DEBUG: Inserting user strengths:", user_strengths)
        for strength in user_strengths:
            cursor.execute("INSERT INTO strengths (name, category_id) VALUES (%s, %s) ON DUPLICATE KEY UPDATE name=name", (strength, strength_category_id))
            cursor.execute("INSERT IGNORE INTO user_strengths (user_id, strength_id) SELECT %s, id FROM strengths WHERE name=%s", (user_id, strength))
    except Exception as e:
        print("ERROR in insert_user_strengths:", e)
        raise e

def insert_business_strengths(cursor, user_id: int, business_strengths: list, business_role_id: int, chat_test_phase_id: int):
    """Insert business strengths. Raises exception on failure."""
    try:
        print("DEBUG: Inserting business strengths:", business_strengths)
        for b_strength in business_strengths:
            cursor.execute("SELECT id, business_phase_id FROM business_strengths WHERE name=%s", (b_strength,))
            phase_result = cursor.fetchone()
            if phase_result and phase_result[1]:
                business_strength_id = phase_result[0]
                business_phase_id = phase_result[1]
            else:
                cursor.execute(
                    "INSERT INTO business_strengths (name, business_role_id, business_phase_id) VALUES (%s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE name=name, business_phase_id=VALUES(business_phase_id), business_role_id=VALUES(business_role_id)",
                    (b_strength, business_role_id, chat_test_phase_id)
                )
                business_strength_id = cursor.lastrowid
                business_phase_id = chat_test_phase_id
            cursor.execute("INSERT IGNORE INTO user_business_strengths (user_id, business_strength_id) VALUES (%s, %s)", (user_id, business_strength_id))
    except Exception as e:
        print("ERROR in insert_business_strengths:", e)
        raise e

def model_update_user_details(user_id: int, user_role: str, user_strengths: list, user_skills: list, business_strengths: list, business_type: str):
    try:
        # Connect to DB
        conn = pymysql.connect(
            host=os.environ["DB_HOST"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASS"],
            database=os.environ["DB_NAME"],
            port=int(os.environ.get("DB_PORT"))
        )
        print("DEBUG: Connected to DB")
        cursor = conn.cursor()

        # Ensure business type and categories
        business_type_id, skill_category_id, strength_category_id = ensure_business_type_and_categories(cursor, business_type)
        
        # Ensure business phase and role
        chat_test_phase_id, business_role_id = ensure_business_phase_and_role(cursor, user_role)
        
        # Insert user skills
        insert_user_skills(cursor, user_id, user_skills, skill_category_id)
        
        # Insert user strengths
        insert_user_strengths(cursor, user_id, user_strengths, strength_category_id)
        
        # Insert business strengths
        insert_business_strengths(cursor, user_id, business_strengths, business_role_id, chat_test_phase_id)

        conn.commit()
        print("DEBUG: DB commit successful")
        cursor.close()
        conn.close()

        return {"status": "success", "message": "User profile updated in database."}
    except Exception as e:
        print("DB ERROR in model_update_user_details:", e)
        return {"status": "error", "message": str(e)}

# Search through the temp directory for the users most recent saved conversation history
def collect_user_history(tool_context: ToolContext):
    """Find the user's most recent conversation history from "__DATE-*.json" files under temp"""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Go up 3 directories
        temp_dir = os.path.join(base_dir, "temp")
        user_id = tool_context.state.get("user_id", "UNKNOWN_USER")
        pattern = rf"tia_responses_{user_id}__DATE-(\d{{8}}_\d{{6}})\.json"
        latest_file = None
        latest_dt = None

        for fname in os.listdir(temp_dir):
            match = re.match(pattern, fname)
            if match:
                dt_str = match.group(1)
                dt = datetime.strptime(dt_str, "%Y%m%d_%H%M%S")
                if latest_dt is None or dt > latest_dt:
                    latest_dt = dt
                    latest_file = fname

        if latest_file is None:
            return {"status": "error", "message": "No conversation history found."}
        filename = os.path.join(temp_dir, latest_file)
        with open(filename, 'r') as f:
            user_history = json.load(f)
        return {"status": "success", "user_history": user_history }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def store_user_profile(tool_context: ToolContext):
    """Store the generated user profile"""
    try:
        state = tool_context.state
        # JOSHUA TODO - Find a way to delete User_History from the state
        #del state["User_History"]
        user_id = state.get("user_id")
        profile = state.get("Generated_Profile")

        # --- DUMMY DATA FOR TESTING ---
        # if not profile.get("User_Strength"):
        #     profile["User_Strength"] = "Leadership, Problem Solving"
        # if not profile.get("User_skills"):
        #     profile["User_skills"] = "Python, Communication, Project Management"
        # if not profile.get("Business_Strength"):
        #     profile["Business_Strength"] = "Innovation, Customer Focus"
        # if not profile.get("Business_Type"):
        #     profile["Business_Type"] = "AI Consulting"
        # --- END DUMMY DATA ---

        user_role = profile.get("UserJob")
        user_strengths = [s.strip() for s in profile.get("User_Strength").split(",") if s.strip()]
        user_skills = [s.strip() for s in profile.get("User_skills").split(",") if s.strip()]
        business_strengths = [s.strip() for s in profile.get("Business_Strength").split(",") if s.strip()]
        business_type = profile.get("Business_Type")
        model_update_user_details(user_id, user_role, user_strengths, user_skills, business_strengths, business_type)

        tool_context.actions.transfer_to_agent = "CoordinatorAgent"
        return {"status": "success", "profile": profile}
    except Exception as e:
        return {"status": "error", "message": str(e)}

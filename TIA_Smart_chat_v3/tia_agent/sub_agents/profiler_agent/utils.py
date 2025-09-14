import pymysql
import os

business_phase_name = "TIA Agent Chatting"

def ensure_business_type_and_categories(cursor, business_type: str, business_category: str, skill_category: str, strength_category: str):
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

        # Ensure business category exists
        cursor.execute("SELECT id FROM business_categories WHERE name=%s", (business_category,))
        result = cursor.fetchone()
        if result:
            business_category_id = result[0]
        else:
            cursor.execute("INSERT INTO business_categories (name) VALUES (%s)", (business_category,))
            business_category_id = cursor.lastrowid
        
        # Ensure skill category exists (fixed column name to business_type_id)
        cursor.execute("SELECT id FROM skill_categories WHERE name=%s", (skill_category,))
        result = cursor.fetchone()
        if result:
            skill_category_id = result[0]
        else:
            cursor.execute(
                "INSERT INTO skill_categories (name, business_type_id) VALUES (%s, %s)", 
                (skill_category, business_type_id)
            )
            skill_category_id = cursor.lastrowid
        
        # Ensure strength category exists
        cursor.execute("SELECT id FROM strength_categories WHERE name=%s", (strength_category,))
        result = cursor.fetchone()
        if result:
            strength_category_id = result[0]
        else:
            cursor.execute("INSERT INTO strength_categories (name) VALUES (%s)", (strength_category,))
            strength_category_id = cursor.lastrowid
        
        return business_category_id, business_type_id, skill_category_id, strength_category_id
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
            cursor.execute("INSERT INTO business_phases (name) VALUES (%s)", (business_phase_name,))
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
    """Insert user skills. Returns list of skill_ids."""
    skill_ids = []
    try:
        print("DEBUG: Inserting user skills:", user_skills)
        for skill in user_skills:
            cursor.execute("INSERT IGNORE INTO skills (name, category_id) VALUES (%s, %s)", (skill, skill_category_id))
            cursor.execute("SELECT id FROM skills WHERE name=%s", (skill,))
            skill_id = cursor.fetchone()[0]
            cursor.execute("INSERT IGNORE INTO user_skills (user_id, skill_id) VALUES (%s, %s)", (user_id, skill_id))
            skill_ids.append(skill_id)
    except Exception as e:
        print("ERROR in insert_user_skills:", e)
        raise e
    return skill_ids

def insert_user_strengths(cursor, user_id: int, user_strengths: list, strength_category_id: int):
    """Insert user strengths. Returns list of strength_ids."""
    strength_ids = []
    try:
        print("DEBUG: Inserting user strengths:", user_strengths)
        for strength in user_strengths:
            cursor.execute("INSERT INTO strengths (name, category_id) VALUES (%s, %s) ON DUPLICATE KEY UPDATE name=name", (strength, strength_category_id))
            cursor.execute("SELECT id FROM strengths WHERE name=%s", (strength,))
            strength_id = cursor.fetchone()[0]
            cursor.execute("INSERT IGNORE INTO user_strengths (user_id, strength_id) VALUES (%s, %s)", (user_id, strength_id))
            strength_ids.append(strength_id)
    except Exception as e:
        print("ERROR in insert_user_strengths:", e)
        raise e
    return strength_ids

def insert_business_skills(cursor, user_id: int, business_skills: list, skill_category_id: int):
    """Insert business skills. Returns list of skill_ids."""
    skill_ids = []
    try:
        print("DEBUG: Inserting business skills:", business_skills)
        for b_skill in business_skills:
            cursor.execute("INSERT INTO skills (name, category_id) VALUES (%s, %s) ON DUPLICATE KEY UPDATE name=name", (b_skill, skill_category_id))
            cursor.execute("SELECT id FROM skills WHERE name=%s", (b_skill,))
            skill_id = cursor.fetchone()[0]
            cursor.execute("INSERT IGNORE INTO user_skills (user_id, skill_id) VALUES (%s, %s)", (user_id, skill_id))
            skill_ids.append(skill_id)
    except Exception as e:
        print("ERROR in insert_business_skills:", e)
        raise e
    return skill_ids

def insert_business_strengths(cursor, user_id: int, business_strengths: list, business_role_id: int, chat_test_phase_id: int):
    """Insert business strengths. Returns list of business_strength_ids."""
    business_strength_ids = []
    try:
        print("DEBUG: Inserting business strengths:", business_strengths)
        for b_strength in business_strengths:
            cursor.execute("SELECT id FROM business_strengths WHERE name=%s", (b_strength,))
            result = cursor.fetchone()
            if result:
                business_strength_id = result[0]
            else:
                cursor.execute(
                    "INSERT INTO business_strengths (name, business_role_id, business_phase_id) VALUES (%s, %s, %s)",
                    (b_strength, business_role_id, chat_test_phase_id)
                )
                business_strength_id = cursor.lastrowid
            cursor.execute("INSERT IGNORE INTO user_business_strengths (user_id, business_strength_id) VALUES (%s, %s)", (user_id, business_strength_id))
            business_strength_ids.append(business_strength_id)
    except Exception as e:
        print("ERROR in insert_business_strengths:", e)
        raise e
    return business_strength_ids
    
#TODO: Update business table
def update_business_info(cursor, user_id: int, business_type_id: int, business_category_id: int, business_phase_id: int, business_name: str):
    """Update the businesses table with correct IDs and phase for the user."""
    try:
        print("DEBUG: Updating business info for user_id:", user_id)
        
        cursor.execute("""
            INSERT INTO businesses (operator_user_id, business_type_id, business_category_id, business_phase_id, name)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                business_type_id = VALUES(business_type_id),
                business_category_id = VALUES(business_category_id),
                business_phase_id = VALUES(business_phase_id),
                name = COALESCE(VALUES(name), name)
        """, (user_id, business_type_id, business_category_id, business_phase_id, business_name))
        
        print("DEBUG: Business info updated successfully")
    except Exception as e:
        print("ERROR in update_business_info:", e)
        raise e


def model_update_user_details(user_id: int, 
                              business_name: str, 
                              user_role: str, 
                              user_strengths: list, 
                              user_skills: list,
                              business_strengths: list, 
                              business_skills: list, 
                              business_type: str, 
                              business_category: str, 
                              skill_category: str, 
                              strength_category: str):
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
        business_category_id, business_type_id, skill_category_id, strength_category_id = ensure_business_type_and_categories(cursor, business_type, business_category, skill_category, strength_category)
        
        # Ensure business phase and role
        chat_test_phase_id, business_role_id = ensure_business_phase_and_role(cursor, user_role)
        
        # Insert user skills
        user_skill_ids = insert_user_skills(cursor, user_id, user_skills, skill_category_id)
        
        # Insert user strengths
        user_strength_ids = insert_user_strengths(cursor, user_id, user_strengths, strength_category_id)

        # Insert business skills
        business_skill_ids = insert_business_skills(cursor, user_id, business_skills, skill_category_id)
        
        # Insert business strengths
        business_strength_ids = insert_business_strengths(cursor, user_id, business_strengths, business_role_id, chat_test_phase_id)

        # Update Business table
        update_business_info(cursor, user_id, business_type_id, business_category_id, chat_test_phase_id, business_name)

        conn.commit()
        print("DEBUG: DB commit successful")
        cursor.close()
        conn.close()

        return {"status": "success", "message": "User profile updated in database."}
    except Exception as e:
        print("DB ERROR in model_update_user_details:", e)
        return {"status": "error", "message": str(e)}
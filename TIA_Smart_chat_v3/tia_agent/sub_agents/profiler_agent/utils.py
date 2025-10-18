import pymysql, os, logging

logger = logging.getLogger(__name__)

business_phase_name = "TIA Agent Chatting"

def ensure_business_type_and_categories(cursor, business_type: str, business_category: str, skill_category: str, strength_category: str):
    """Ensure business type, skill category, and strength category exist. Returns IDs or raises exception."""
    try:
        logger.debug("Ensuring business type and categories for: %s", business_type)
        
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
        logger.error("ERROR in ensure_business_type_and_categories: %s", e)
        raise e

def ensure_business_phase_and_role(cursor, user_role: str):
    """Ensure business phase and role exist. Returns IDs or raises exception."""
    try:
        logger.debug("Ensuring business phase and role")
        
        # Ensure business phase exists
        cursor.execute("SELECT id FROM business_phases WHERE name=%s", ("TIA Agent Chatting",))
        result = cursor.fetchone()
        if result:
            business_phase_id = result[0]
        else:
            cursor.execute("INSERT INTO business_phases (name) VALUES (%s)", (business_phase_name,))
            business_phase_id = cursor.lastrowid
        
        # Ensure business role exists
        cursor.execute("SELECT id FROM business_roles WHERE name=%s", (user_role,))
        result = cursor.fetchone()
        if result:
            business_role_id = result[0]
        else:
            cursor.execute("INSERT INTO business_roles (name) VALUES (%s)", (user_role,))
            business_role_id = cursor.lastrowid
        
        return business_phase_id, business_role_id
    except Exception as e:
        logger.error("ERROR in ensure_business_phase_and_role: %s", e)
        raise e

def insert_user_skills(cursor, user_id: int, user_skills: list, skill_category_id: int):
    """Insert user skills. Returns list of skill_ids."""
    skill_ids = []
    try:
        logger.debug("Inserting user skills: %s", user_skills)
        for skill in user_skills:
            cursor.execute("INSERT IGNORE INTO skills (name, category_id) VALUES (%s, %s)", (skill, skill_category_id))
            cursor.execute("SELECT id FROM skills WHERE name=%s", (skill,))
            skill_id = cursor.fetchone()[0]
            cursor.execute("INSERT IGNORE INTO user_skills (user_id, skill_id) VALUES (%s, %s)", (user_id, skill_id))
            skill_ids.append(skill_id)
    except Exception as e:
        logger.error("ERROR in insert_user_skills: %s", e)
        raise e
    return skill_ids

def insert_user_strengths(cursor, user_id: int, user_strengths: list, strength_category_id: int):
    """Insert user strengths. Returns list of strength_ids."""
    strength_ids = []
    try:
        logger.debug("Inserting user strengths:", user_strengths)
        for strength in user_strengths:
            cursor.execute("INSERT INTO strengths (name, category_id) VALUES (%s, %s) ON DUPLICATE KEY UPDATE name=name", (strength, strength_category_id))
            cursor.execute("SELECT id FROM strengths WHERE name=%s", (strength,))
            strength_id = cursor.fetchone()[0]
            cursor.execute("INSERT IGNORE INTO user_strengths (user_id, strength_id) VALUES (%s, %s)", (user_id, strength_id))
            strength_ids.append(strength_id)
    except Exception as e:
        logger.debug("ERROR in insert_user_strengths:", e)
        raise e
    return strength_ids

def insert_business_strengths(cursor, user_id: int, business_strengths: list, business_role_id: int, business_phase_id: int):
    """Insert business strengths. Returns list of business_strength_ids."""
    business_strength_ids = []
    try:
        logger.debug("Inserting business strengths: %s", business_strengths)
        for b_strength in business_strengths:
            cursor.execute("SELECT id FROM business_strengths WHERE name=%s", (b_strength,))
            result = cursor.fetchone()
            if result:
                business_strength_id = result[0]
            else:
                cursor.execute(
                    "INSERT INTO business_strengths (name, business_role_id, business_phase_id) VALUES (%s, %s, %s)",
                    (b_strength, business_role_id, business_phase_id)
                )
                business_strength_id = cursor.lastrowid
            cursor.execute("INSERT IGNORE INTO user_business_strengths (user_id, business_strength_id) VALUES (%s, %s)", (user_id, business_strength_id))
            business_strength_ids.append(business_strength_id)
    except Exception as e:
        logger.debug("ERROR in insert_business_strengths: %s", e)
        raise e
    return business_strength_ids
    
def update_business_info(cursor, user_id: int, business_type_id: int, business_category_id: int, business_phase_id: int):
    """Update the existing businesses table row with correct IDs, phase, and name for the user."""
    try:
        logger.debug("Updating business info for user_id: %s", user_id)

        cursor.execute("""
            UPDATE businesses 
            SET business_type_id = %s, business_category_id = %s, business_phase_id = %s
            WHERE operator_user_id = %s
        """, (business_type_id, business_category_id, business_phase_id, user_id))

        logger.debug("Business info updated successfully")
        return True
    except Exception as e:
        logger.error("ERROR in update_business_info: %s", e)
        return False

def model_update_user_details(user_id: int, 
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
        logger.debug(f"Connected {user_id} to Database for updating user details")
        cursor = conn.cursor()

        # Ensure business type and categories
        business_category_id, business_type_id, skill_category_id, strength_category_id = ensure_business_type_and_categories(cursor, business_type, business_category, skill_category, strength_category)
        
        # Ensure business phase and role
        business_phase_id, business_role_id = ensure_business_phase_and_role(cursor, user_role)
        
        # Insert user skills
        insert_user_skills(cursor, user_id, user_skills, skill_category_id)
        
        # Insert user strengths
        insert_user_strengths(cursor, user_id, user_strengths, strength_category_id)
        
        # Insert business strengths
        insert_business_strengths(cursor, user_id, business_strengths, business_role_id, business_phase_id)

        # Update Business table
        if not update_business_info(cursor, user_id, business_type_id, business_category_id, business_phase_id):
            raise Exception("Failed to update business info")

        conn.commit()
        logger.debug("DB commit successful")
        cursor.close()
        conn.close()

        return True
    except Exception as e:
        logger.error("DB ERROR in model_update_user_details: %s", e)
        return False
from pydantic import BaseModel, Field
from typing import Optional

class ProfileOutputSchema(BaseModel):
    """Schema for generated user profile information"""
    Business_Type: Optional[str] = Field(description="The user's business type", max_length=100)
    UserJob: str = Field(description="The user's job or role", max_length=100)
    User_Strength: str = Field(description="The user's main strength", max_length=100)
    User_skills: str = Field(description="The user's skills", max_length=100)
    Business_Strength: str = Field(description="The user's job business strength", max_length=100)
    Business_Category: str = Field(description="The user's business category", max_length=100)
    Skill_Category: str = Field(description="The user's skill category", max_length=100)
    Strength_Category: str = Field(description="The user's strength category", max_length=100)
    
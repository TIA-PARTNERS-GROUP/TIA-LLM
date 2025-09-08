from pydantic import BaseModel, Field
from typing import Optional

class ProfileOutputSchema(BaseModel):
    """Schema for generated user profile information"""
    Business_Name: str = Field(description="The user's business idea")
    Business_Type: Optional[str] = Field(description="The user's business type")
    UserJob: str = Field(description="The user's job or role")
    User_Strength: str = Field(description="The user's main strength")
    User_skills: str = Field(description="The user's skills")
    Business_Strength: str = Field(description="The user's job business strength")
    
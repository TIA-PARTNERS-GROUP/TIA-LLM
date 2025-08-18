from pydantic import BaseModel, Field
from typing import Optional

class ProfileOutputSchema(BaseModel):
    """Schema for generated user profile information"""
    User: str = Field(description="The user's name")
    Idea: str = Field(description="The user's business idea")
    UserPost: str = Field(description="The user's job title or post")
    Strength: str = Field(description="The user's main strength")